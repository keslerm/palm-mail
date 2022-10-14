use strict;
use DBI;
use Palm;
use Data::Dumper;
use Palm::PDB;
use Palm::Mail;
use Time::Piece;

# Open the blank database for now
my $pdb = new Palm::PDB;
$pdb->Load("MailDB.pdb");

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

# Read the records
for (@{ $pdb->{'records'} }) {
      # Just do outbound import now
      if ($_->{category} == 1) {
            my $query = $dbh->prepare("insert into emails (id, to_email, from_email, subject, body, category) values (?, ?, ?, ?, ?, ?)");
            $query->bind_param(1, $_->{id});
            $query->bind_param(2, $_->{to});
            $query->bind_param(3, $_->{from});
            $query->bind_param(4, $_->{subject});
            $query->bind_param(5, $_->{body});
            $query->bind_param(6, $_->{category});
            $query->execute() or die $DBI::errstr;
      }
}

# quit the database
#$dbh->disconnect();

