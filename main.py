# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import jwt, JWTError
import httpx

app = FastAPI()

KEYCLOAK_URL = "http://localhost:8080"
REALM = "myrealm"
CLIENT_ID = "myapp"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
)

# Fetch Keycloak public keys
async def get_jwks():
    async with httpx.AsyncClient() as client:
        response = await client.get(JWKS_URL)
        return response.json()

# Validate and decode the JWT token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)

        # Find the matching key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "n": key["n"],
                    "e": key["e"],
                }

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token key")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=ISSUER,
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )

# --- Routes ---

@app.get("/")
def public_route():
    return {"message": "This is public"}

@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {
        "message": "You are authenticated!",
        "username": user.get("preferred_username"),
        "email": user.get("email"),
    }