import json
import datetime
import logging
import hashlib
import uuid

from http.server import BaseHTTPRequestHandler

from homework_05.scoring import get_interests, get_score
from homework_05.store import Store
from homework_05.validation import (
    Validatable,
    ClientIDsField,
    DateField,
    CharField,
    EmailField,
    PhoneField,
    BirthDayField,
    GenderField,
    ArgumentsField,
    GENDERS,
)

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}


class ClientsInterestsRequest(Validatable):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Validatable):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def post_validate(self):
        """
        phone-email, first name-lastname, gender-birthday с непустыми значениями.
        :return:
        """
        if not (
            all((self.phone, self.email))
            or all((self.first_name, self.last_name))
            or all((self.gender in GENDERS, self.birthday))
        ):
            raise ValueError("Please provide correct request params")


class MethodRequest(Validatable):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + SALT).encode("utf-8")
        ).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    method_request: MethodRequest = MethodRequest.validate(request.get("body"))
    if not method_request.is_valid:
        return str(method_request.validation_errors), 422

    if not check_auth(method_request):
        return "Forbidden", 403

    match method_request.method:
        case "online_score":
            online_score_args: OnlineScoreRequest = OnlineScoreRequest.validate(
                method_request.arguments
            )
            ctx["has"] = online_score_args.has

            if not online_score_args.is_valid:
                return str(online_score_args.validation_errors), 422

            if method_request.is_admin:
                return {"score": 42}, 200

            return {
                "score": get_score(
                    store=store,
                    phone=online_score_args.phone,
                    email=online_score_args.email,
                    birthday=online_score_args.birthday,
                    gender=online_score_args.gender,
                    first_name=online_score_args.first_name,
                    last_name=online_score_args.last_name,
                )
            }, 200
        case "clients_interests":
            clients_interests_args: ClientsInterestsRequest = (
                ClientsInterestsRequest.validate(method_request.arguments)
            )

            if not clients_interests_args.is_valid:
                return str(method_request.validation_errors), 422

            ctx["nclients"] = len(clients_interests_args.client_ids)

            return {
                f"{client_id}": get_interests(store, client_id)
                for client_id in clients_interests_args.client_ids
            }, 200


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store: Store | None = None

    def get_store(self) -> Store:
        if not self.store:
            raise AttributeError("Cache store is not instantiated!")
        return self.store

    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        data_string: bytes | None = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except Exception as e:
            logging.error(f"Error on json request parsing {e}")
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %r %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers},
                        context,
                        self.get_store(),
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))
