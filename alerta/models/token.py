import datetime
from typing import Any, Dict

import jwt
from flask import current_app, request
from jwt import DecodeError, ExpiredSignature, InvalidAudience

dt = datetime.datetime


class Jwt:
    """
    JSON Web Token (JWT): https://tools.ietf.org/html/rfc7519
    """

    def __init__(self, iss: str, typ: str, sub: str, aud: str, exp: dt, nbf: dt, iat: dt, jti: str=None, **kwargs) -> None:

        self.issuer = iss
        self.type = typ
        self.subject = sub
        self.audience = aud
        self.expiration = exp
        self.not_before = nbf
        self.issued_at = iat
        self.jwt_id = jti

        self.name = kwargs.get('name', None)
        self.preferred_username = kwargs.get('preferred_username', None)
        self.email = kwargs.get('email', None)
        self.provider = kwargs.get('provider', None)
        self.scopes = kwargs.get('scopes', list())
        self.email_verified = kwargs.get('email_verified', None)
        self.customers = kwargs.get('customers', None)

        setattr(self, current_app.config['OIDC_CUSTOM_CLAIM'], kwargs.get(current_app.config['OIDC_CUSTOM_CLAIM']))

    @classmethod
    def parse(cls, token: str, key: str=None, verify: bool=True, algorithm: str='HS256') -> 'Jwt':
        try:
            json = jwt.decode(
                token,
                key=key or current_app.config['SECRET_KEY'],
                verify=verify,
                algorithms=algorithm,
                audience=current_app.config['OAUTH2_CLIENT_ID'] or request.url_root
            )
        except (DecodeError, ExpiredSignature, InvalidAudience):
            raise

        kwargs = dict([(current_app.config['OIDC_CUSTOM_CLAIM'], json.get(current_app.config['OIDC_CUSTOM_CLAIM'], []))])

        return Jwt(
            iss=json.get('iss', None),
            typ=json.get('typ', None),
            sub=json.get('sub', None),
            aud=json.get('aud', None),
            exp=json.get('exp', None),
            nbf=json.get('nbf', None),
            iat=json.get('iat', None),
            jti=json.get('jti', None),
            name=json.get('name', None),
            preferred_username=json.get('preferred_username', None),
            email=json.get('email', None),
            provider=json.get('provider', None),
            scopes=json.get('scope', '').split(' '),  # eg. scope='read write' => scopes=['read', 'write']
            email_verified=json.get('email_verified', None),
            customers=[json['customer']] if 'customer' in json else json.get('customers', list()),
            **kwargs
        )

    @property
    def serialize(self) -> Dict[str, Any]:
        data = {
            'iss': self.issuer,
            'typ': self.type,
            'sub': self.subject,
            'aud': self.audience,
            'exp': self.expiration,
            'nbf': self.not_before,
            'iat': self.issued_at,
            'jti': self.jwt_id
        }
        if self.name:
            data['name'] = self.name
        if self.preferred_username:
            data['preferred_username'] = self.preferred_username
        if self.email:
            data['email'] = self.email
        if self.email_verified is not None:
            data['email_verified'] = self.email_verified
        if self.provider:
            data['provider'] = self.provider
        if self.scopes:
            data['scope'] = ' '.join(self.scopes)

        if current_app.config['CUSTOMER_VIEWS']:
            data['customers'] = self.customers

        if current_app.config['OIDC_CUSTOM_CLAIM']:
            data[current_app.config['OIDC_CUSTOM_CLAIM']] = getattr(self, current_app.config['OIDC_CUSTOM_CLAIM'])

        return data

    @property
    def tokenize(self) -> str:
        token = jwt.encode(self.serialize, key=current_app.config['SECRET_KEY'])
        return token.decode('unicode_escape')

    def __repr__(self) -> str:
        return 'Jwt(iss={!r}, sub={!r}, aud={!r}, exp={!r}, name={!r}, preferred_username={!r}, customers={!r})'.format(
            self.issuer, self.subject, self.audience, self.expiration, self.name, self.preferred_username, self.customers
        )
