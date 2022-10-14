from imapclient import IMAPClient
import os, sys, argparse, subprocess
import sqlite3
import email.parser

db = sqlite3.connect("email.db")


def addressString(entry):
    if entry.name != None:
        return "%s <%s@%s>" % (
            entry.name.decode(),
            entry.mailbox.decode(),
            entry.host.decode(),
        )
    else:
        return "%s@%s" % (entry.mailbox.decode(), entry.host.decode())


def setupDatabase():
    table = """CREATE TABLE emails (
    id int,
    from_email varchar,
    to_email varchar,
    subject varchar,
    body varchar,
    timestamp text,
    is_read bool
  ); """

    cur = db.cursor()
    cur.execute(table)
    db.commit()
    db.close()

    print("Database is setup")


def fetchEmail():
    # context manager ensures the session is cleaned up
    with IMAPClient(host=os.environ["EMAIL_HOST"]) as client:
        client.login(os.environ["EMAIL_USERNAME"], os.environ["EMAIL_PASSWORD"])
        client.select_folder("INBOX")

        # search criteria are passed in a straightforward way
        # (nesting is supported)
        messages = client.search(["ALL"])

        # fetch selectors are passed as a simple list of strings.
        response = client.fetch(
            messages,
            ["FLAGS", "RFC822.SIZE", "ENVELOPE", "INTERNALDATE", "BODY.PEEK[]"],
        )

        # `response` is keyed by message id and contains parsed,
        # converted response items.
        messages = []
        for message_id, data in response.items():
            envelope = data[b"ENVELOPE"]
            read = b"\\Seen" in data[b"FLAGS"]

            if os.environ.get("EMAIL_DEBUG"):
                print("=====START")
                # print(data[b'BODY[TEXT]'])
                print("ID: %s" % (message_id))
                print("FROM: %s" % (addressString(envelope.from_[0])))
                print("TO: %s" % (addressString(envelope.to[0])))
                print("SUBJECT %s" % (envelope.subject.decode()))
                print("DATE: %s" % (envelope.date))
                print(data[b"FLAGS"])
                print("read? %s" % (read))
                print("=====END")


            # Some email parsing because email is amazingly crazy
            body = ""
            fullEmail = email.message_from_bytes(data[b'BODY[]'])
            for part in fullEmail.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload()

            if os.environ.get("EMAIL_DEBUG"):
                print(body)

            messages.append(
                {
                    "id": message_id,
                    "from": addressString(envelope.from_[0]),
                    "to": addressString(envelope.to[0]),
                    "subject": envelope.subject.decode(),
                    "timestamp": envelope.date,
                    "is_read": read,
                    "body": body,
                }
            )

        return messages


def sync():
    # remove existing MailDB file
    try:
        os.remove("MailDB.pdb")
    except:
        None

    # import new emails
    print("Fetching emails")
    emails = fetchEmail()

    cur = db.cursor()

    print("Caching in local database")
    for email in emails:
        cur.execute(
            "insert into emails (id, from_email, to_email, subject, body, is_read, timestamp) values (?, ?, ?, ?, ?, ?, ?)",
            (
                email["id"],
                email["from"],
                email["to"],
                email["subject"],
                email["body"],
                email["is_read"],
                email["timestamp"],
            ),
        )

    db.commit()
    db.close()

    # Generate the new PDB file
    print("Generating PDB file")
    subprocess.run(["perl", "generate_pdb.pl"])

def main(argv):
    # Initialize parser
    parser = argparse.ArgumentParser()

    parser.add_argument("command", help="Setup database")

    # Adding optional argument
    parser.add_argument("-o", "--Output", help="Show Output")

    # Read arguments from command line
    args = parser.parse_args()

    if args.command == "init":
        print("Setting up database...")
        setupDatabase()
    elif args.command == "sync":
        sync()
    elif args.command == "test":
        fetchEmail()


if __name__ == "__main__":
    main(sys.argv)
