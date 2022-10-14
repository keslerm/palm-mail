from imapclient import IMAPClient
import os, sys, argparse, subprocess
import sqlite3
import email.parser
import smtplib
from email import policy
from smtplib import SMTP_SSL
from email.message import EmailMessage

db = sqlite3.connect("email.db")

# Hardcode the default category list.
CATEGORIES = {
    "Inbox": 0,
    "Outbox": 1,
    "Deleted": 2,
    "Filed": 3,
    "Draft": 4,
}


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
    id int primary key,
    from_email varchar,
    to_email varchar,
    subject varchar,
    body varchar,
    timestamp text,
    is_read bool,
    category int
  ); """

    cur = db.cursor()
    cur.execute(table)
    db.commit()
    db.close()

    print("Database is setup")


def clearDatabase():
    cur = db.cursor()
    cur.execute("delete from emails")
    db.commit()


def fetchEmail():
    # context manager ensures the session is cleaned up
    with IMAPClient(host=os.environ["EMAIL_HOST"]) as client:
        client.login(os.environ["EMAIL_USERNAME"], os.environ["EMAIL_PASSWORD"])
        client.select_folder("INBOX")

        # search criteria are passed in a straightforward way
        # (nesting is supported)
        messages = client.search(["ALL"], "UTF-8")

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

            """
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
            """

            # Some email parsing because email is amazingly crazy
            body = ""
            fullEmail = email.message_from_bytes(data[b"BODY[]"], policy=policy.default)
            print(fullEmail.get("From"))
            for part in fullEmail.walk():
                print(part.get_content_type())
                if part.get_content_type() == "text/plain":
                    body = cleanBody(part.get_payload(decode=True))

            message = {
                "id": message_id,
                "from": clean(fullEmail.get("From")),
                "to": clean(fullEmail.get("To")),
                "subject": clean(fullEmail.get("Subject")),
                "timestamp": envelope.date,
                "is_read": read,
                "body": body,
            }

            messages.append(message)

            if os.environ.get("EMAIL_DEBUG"):
                print("====================START")
                print(f"ID: {message['id']}")
                print(f"FROM: {message['from']}")
                print(f"TO: {message['to']}")
                print(f"SUBJECT: {message['subject']}")
                print(f"TIMESTAMP: {message['timestamp']}")
                print(f"IS_READ: {message['is_read']}")
                print("BODY:")
                print(body)
                print("====================END")

        return messages


def cleanBody(body):
    """
    Attempt to strip every bit of unicode out as well as fixing the line endings since Palm
    expects unix endings but the library gives me windows endings.
    """

    # replacement strings
    WINDOWS_LINE_ENDING = "\r\n"
    UNIX_LINE_ENDING = "\n"

    result = body.decode("utf-8", "ignore").replace(
        WINDOWS_LINE_ENDING, UNIX_LINE_ENDING
    )
    return result


def clean(string):

    return string.encode("ascii", "ignore").decode()


def send():
    # check for outbox emailsgg
    cur = db.cursor()

    rows = cur.execute(
        "select id, from_email, to_email, subject, body from emails where category = 1"
    )

    with SMTP_SSL(host=os.environ.get("EMAIL_HOST"), port=465) as server:
        server.login(os.environ.get("EMAIL_USERNAME"), os.environ.get("EMAIL_PASSWORD"))
        server.set_debuglevel(1)
        for row in rows.fetchall():
            print(f"sending {row[0]}")
            msg = EmailMessage()

            msg["To"] = row[2]
            msg["From"] = os.environ.get("EMAIL_USERNAME")
            msg["Subject"] = row[3]
            msg.set_content(row[4])
            print(msg)

            server.send_message(msg)
            # remove from outbox
            cur.execute("delete from emails where id = ?", (row[0],))

        server.quit()


def sync():
    # remove entries for now
    clearDatabase()

    # import new emails
    print("Fetching emails")
    emails = fetchEmail()

    cur = db.cursor()

    print("Caching in local database")
    for email in emails:
        cur.execute(
            "insert into emails (id, from_email, to_email, subject, body, is_read, timestamp, category) values (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                email["id"],
                email["from"],
                email["to"],
                email["subject"],
                email["body"],
                email["is_read"],
                email["timestamp"],
                CATEGORIES["Inbox"],
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
    elif args.command == "send":
        send()
    elif args.command == "test":
        fetchEmail()


if __name__ == "__main__":
    main(sys.argv)
