import { createRemoteJWKSet, jwtVerify } from "jose";

type ControllerAccessFailure = {
  status: number;
  detail: string;
};

const jwksByIssuer = new Map<string, ReturnType<typeof createRemoteJWKSet>>();

export async function controllerIdentity(
  request: Request,
): Promise<string | ControllerAccessFailure> {
  const issuer = process.env.CF_ACCESS_TEAM_DOMAIN;
  const audience = process.env.CF_ACCESS_AUD;
  const allowedEmails = process.env.CF_ACCESS_ALLOWED_EMAILS;
  if (!issuer || !audience || !allowedEmails) {
    return { status: 503, detail: "Controller Access validation is not configured." };
  }

  const assertion = request.headers.get("cf-access-jwt-assertion");
  if (!assertion) {
    return { status: 401, detail: "Controller authentication is required." };
  }

  try {
    const jwks = getJwks(issuer);
    const { payload } = await jwtVerify(assertion, jwks, { issuer, audience });
    if (typeof payload.email !== "string" || payload.email.length === 0) {
      return { status: 403, detail: "Controller identity is missing from Access." };
    }
    const email = payload.email.toLowerCase();
    const allowed = allowedEmails.split(",").map((value) => value.trim().toLowerCase());
    if (!allowed.includes(email)) {
      return { status: 403, detail: "This Access identity cannot publish controller decisions." };
    }
    return email;
  } catch {
    return { status: 403, detail: "Controller authentication could not be verified." };
  }
}

function getJwks(issuer: string) {
  let jwks = jwksByIssuer.get(issuer);
  if (!jwks) {
    jwks = createRemoteJWKSet(new URL("/cdn-cgi/access/certs", issuer));
    jwksByIssuer.set(issuer, jwks);
  }
  return jwks;
}
