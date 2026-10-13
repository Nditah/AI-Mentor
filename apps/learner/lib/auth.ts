type TokenSource = () => Promise<string | null>;

let source: TokenSource | null = null;

export function setTokenSource(next: TokenSource | null) {
  source = next;
}

export async function sessionToken(): Promise<string | null> {
  return source ? source() : null;
}
