import time
from typing import List, Optional, Tuple

from grpc import ssl_channel_credentials
from grpc.aio import (
    ClientCallDetails,
    UnaryStreamClientInterceptor,
    UnaryUnaryClientInterceptor,
    secure_channel,
)
from solders.keypair import Keypair

from jito_searcher_client.generated.auth_pb2 import (
    GenerateAuthChallengeRequest,
    GenerateAuthTokensRequest,
    GenerateAuthTokensResponse,
    RefreshAccessTokenRequest,
    RefreshAccessTokenResponse,
    Role,
)
from jito_searcher_client.generated.auth_pb2_grpc import AuthServiceStub
from jito_searcher_client.generated.searcher_pb2_grpc import SearcherServiceStub
from jito_searcher_client.token import JwtToken


class AsyncSearcherInterceptor(
    UnaryUnaryClientInterceptor,
    UnaryStreamClientInterceptor,
):
    """
    AsyncSearcherInterceptor is responsible for authenticating with the block engine.
    Authentication happens in a challenge-response handshake.
    1. Request a challenge and provide your public key.
    2. Get challenge and sign a message "{pubkey}-{challenge}".
    3. Get back a refresh token and access token.

    When the access token expires, use the refresh token to get a new one.
    When the refresh token expires, perform the challenge-response handshake again.
    """

    def __init__(self, url: str, kp: Keypair):
        """

        :param url: url of the Block Engine without http or https.
        :param kp: block engine authentication keypair
        """
        self._url = url
        self._kp = kp

        self._access_token: Optional[JwtToken] = None
        self._refresh_token: Optional[JwtToken] = None

    async def intercept_unary_stream(
        self,
        continuation,
        client_call_details,
        request,
    ):
        await self.authenticate_if_needed()

        client_call_details = self._insert_headers(
            [("authorization", f"Bearer {self._access_token.token}")],
            client_call_details,
        )

        call = await continuation(client_call_details, request)
        return call

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        await self.authenticate_if_needed()

        client_call_details = self._insert_headers(
            [("authorization", f"Bearer {self._access_token.token}")],
            client_call_details,
        )

        call = await continuation(client_call_details, request)
        return call

    def _insert_headers(self, headers, client_call_details: ClientCallDetails):
        new_metadata = []
        if client_call_details.metadata is not None:
            new_metadata = list(client_call_details.metadata)
        new_metadata.extend(headers)
        client_call_details = ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            new_metadata,
            client_call_details.credentials,
            client_call_details.wait_for_ready,
            client_call_details.compression,
        )
        return client_call_details

    async def authenticate_if_needed(self):
        if self._access_token is None or self._access_token.is_expired():
            await self.full_authentication()
        elif self._refresh_token.is_expired():
            await self.full_authentication()
        else:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        credentials = ssl_channel_credentials()
        channel = secure_channel(self._url, credentials)
        auth_client = AuthServiceStub(channel)

        refresh_token_response: RefreshAccessTokenResponse = await auth_client.RefreshAccessToken(
            RefreshAccessTokenRequest(refresh_token=self._refresh_token.token)
        )

        self._access_token = JwtToken(
            token=refresh_token_response.access_token.value,
            expiration=refresh_token_response.access_token.expires_at_utc.seconds,
        )

    async def full_authentication(self):
        credentials = ssl_channel_credentials()
        channel = secure_channel(self._url, credentials)
        auth_client = AuthServiceStub(channel)

        challenge = (
            await auth_client.GenerateAuthChallenge(
                GenerateAuthChallengeRequest(role=Role.SEARCHER, pubkey=bytes(self._kp.pubkey()))
            )
        ).challenge

        challenge_to_sign = f"{str(self._kp.pubkey())}-{challenge}"

        signed = self._kp.sign_message(bytes(challenge_to_sign, "utf8"))

        auth_tokens_response: GenerateAuthTokensResponse = await auth_client.GenerateAuthTokens(
            GenerateAuthTokensRequest(
                challenge=challenge_to_sign,
                client_pubkey=bytes(self._kp.pubkey()),
                signed_challenge=bytes(signed),
            )
        )

        self._access_token = JwtToken(
            token=auth_tokens_response.access_token.value,
            expiration=auth_tokens_response.access_token.expires_at_utc.seconds,
        )

        self._refresh_token = JwtToken(
            token=auth_tokens_response.refresh_token.value,
            expiration=auth_tokens_response.refresh_token.expires_at_utc.seconds,
        )


async def get_async_searcher_client(url: str, kp: Keypair) -> SearcherServiceStub:
    """
    Returns a Searcher Service client that intercepts requests and authenticates with the block engine.
    :param url: url of the block engine without http/https
    :param kp: keypair of the block engine
    :return: SearcherServiceStub which handles authentication on requests
    """
    # Authenticate immediately
    searcher_interceptor = AsyncSearcherInterceptor(url, kp)
    await searcher_interceptor.authenticate_if_needed()

    credentials = ssl_channel_credentials()
    channel = secure_channel(url, credentials, interceptors=[searcher_interceptor])
    channel._unary_stream_interceptors.append(searcher_interceptor)

    return SearcherServiceStub(channel)

async def get_async_searcher_client_no_auth(url: str) -> SearcherServiceStub:
    """
    Returns a Searcher Service client that connects without authentication.
    :param url: url of the block engine without http/https
    :return: SearcherServiceStub without authentication
    """
    credentials = ssl_channel_credentials()
    channel = secure_channel(url, credentials)
    return SearcherServiceStub(channel)
