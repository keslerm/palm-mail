use strict;
use DBI;
use Palm;
use Palm::PDB;
use Palm::Mail;
use Time::Piece;

# Open the blank database for now
my $pdb = new Palm::PDB;
$pdb->Load("assets/MailDB.pdb.blank");

# Create mailer helper
my $mailer = new Palm::Mail;

# define database name and driver
my $dbd = "DBI:SQLite:dbname=email.db";

# create and connect to a database.
# this will create a file named xmodulo.db
my $dbh = DBI->connect($dbd, "", "", { RaiseError => 1 })
                      or die $DBI::errstr;
print STDERR "Database opened successfully\n";

# search and iterate row(s) in the table
my $obj = $dbh->prepare("SELECT * from emails");
my $ret = $obj->execute() or die $DBI::errstr;

if($ret < 0) {
   print STDERR $DBI::errstr;
}

while(my @row = $obj->fetchrow_array()) {
      my $email = $mailer->new_Record;

      # store email id for upwards sync
      $email->{id} = $row[0];
      $email->{from} = $row[1];
      $email->{to} = $row[2];
      $email->{subject} = $row[3];
      $email->{body} = $row[4];
      $email->{is_read} = $row[6];

      # the format for dates is to store each item individually so split taht up here
      my $dt = Time::Piece->strptime($row[5], "%F %T");

      $email->{year} = $dt->year;
      $email->{month} = $dt->mon;
      $email->{day} = $dt->mday;
      $email->{hour} = $dt->hour;
      $email->{minute} = $dt->min;

      $pdb->append_Record($email);
}

# quit the database
$dbh->disconnect();

# Write the new mail database
$pdb->Write("MailDB.pdb");
