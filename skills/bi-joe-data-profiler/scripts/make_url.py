"""Builds a connection URL for BI Joe, so nobody has to hand-encode one.

    python make_url.py sqlserver --server "myhost\\SQLEXPRESS" --database Sales --windows-auth
    python make_url.py sqlserver --server myserver.database.windows.net --database Sales \\
                                 --user joe --password-env MSSQL_PWD
    python make_url.py drivers          # which SQL Server ODBC drivers this Python can see

The URL is printed to stdout. Put it in single quotes when you pass it to `run_bijoe.py profile`.
A password is never written into the URL: use --password-env and BI Joe reads the environment
variable at run time. Other databases use plain URLs, see references/connecting.md.
"""

import argparse
import sys
from urllib.parse import quote_plus


def sqlserver(args: argparse.Namespace) -> str:
    parts = [f"DRIVER={{{args.driver}}}", f"SERVER={args.server}"]
    if args.database:
        parts.append(f"DATABASE={args.database}")
    if args.windows_auth:
        parts.append("Trusted_Connection=yes")
    else:
        if not args.user or not args.password_env:
            sys.exit("error: use --windows-auth, or give --user and --password-env (the NAME of an environment variable "
                     "that holds the password, never the password itself)")
        parts += [f"UID={args.user}", "PWD=${" + args.password_env + "}"]
    if not args.no_trust_cert:
        parts.append("TrustServerCertificate=yes")
    if args.encrypt is not None:
        parts.append(f"Encrypt={'yes' if args.encrypt else 'no'}")
    return "mssql+pyodbc:///?odbc_connect=" + quote_plus(";".join(parts))


def drivers() -> None:
    try:
        import pyodbc
    except ImportError:
        sys.exit("pyodbc is not installed. Run: pip install pyodbc")
    found = [d for d in pyodbc.drivers() if "SQL Server" in d]
    if not found:
        sys.exit("No SQL Server ODBC driver found. Install 'ODBC Driver 18 for SQL Server' from Microsoft.")
    print("\n".join(found))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="kind", required=True)
    s = sub.add_parser("sqlserver", help="SQL Server or Azure SQL through ODBC")
    s.add_argument("--server", required=True, help=r"host, host\instance or host,port")
    s.add_argument("--database", help="database name")
    s.add_argument("--windows-auth", action="store_true", help="sign in with the current Windows account")
    s.add_argument("--user", help="SQL login name")
    s.add_argument("--password-env", help="name of the environment variable that holds the password")
    s.add_argument("--driver", default="ODBC Driver 18 for SQL Server")
    s.add_argument("--no-trust-cert", action="store_true", help="do not trust the server certificate (use for servers with a proper certificate)")
    s.add_argument("--encrypt", type=lambda v: v.lower() in ("1", "true", "yes"), help="force Encrypt=yes/no")
    sub.add_parser("drivers", help="list the SQL Server ODBC drivers this Python can see")
    args = p.parse_args()
    if args.kind == "drivers":
        drivers()
    else:
        print(sqlserver(args))


if __name__ == "__main__":
    main()
