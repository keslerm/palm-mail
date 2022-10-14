# Palm IMAP Sync

This is a really messy tool for syncing an IMAP email Inbox into a format supported by the Palm mail app. This only works for the original Mail app, not the Versamail or whatever app they ended up pivoting too later.

This is at best a hacky proof of concept. 

Why did I make this? Because science isn't about WHY it's about WHY NOT.

## Requirements

* [Pilot Link](https://github.com/desrod/pilot-link) - Specifically pilot-xfer to sync the mailbox file
* Perl - Including the following dependencies
  * [Palm::PDB](https://metacpan.org/pod/Palm::PDB)
  * [Palm::Mail](https://metacpan.org/pod/Palm::Mail)
  * [DBD::SQLite](https://metacpan.org/pod/DBD::SQLite) This one is probably already in your distros package repository
* Python3 - Including the following dependencies
  * [IMAPClient](https://pypi.org/project/IMAPClient/)

## Usage

Configure these environmental variables:

```
export EMAIL_HOST="your.host.com"
export EMAIL_USERNAME="username"
export EMAIL_PASSWORD="password"
```

Then initialize a blank email database which is used to store your email data for generating the Palm database.

```
python3 palm-mail.py init
```

Then sync your emails and generate the database for your Palm

```
python3 palm-mail.py sync
```

Lastly, push your MailDB.pdb file to your actual Palm device. The port value in the following will vary depending on your device so just configure that as needed:

```
sudo pilot-xfer -p /dev/ttyUSB1 -i MailDB.pdb 
```

And now you should have your email in your Palms Mail app!
