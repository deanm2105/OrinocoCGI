#!/usr/bin/perl -w

# Orinoc Stage 3 - CGI Version
# By Dean McGregor

use CGI qw/:all/;

if (@ARGV == 0) {
	use CGI::Carp qw(fatalsToBrowser carpout);
	open(LOG, ">>./warnings") or die "Cannot open errors $!";
	carpout(*LOG);
}

$bookFile = "books.json";

sub initProgram() {
	if (!(-d "./orders")) {
		mkdir "./orders";
		#create the file to store the next order number
		open (NEXTNUM, ">./orders/NEXT_ORDER_NUMBER");
		print NEXTNUM "0";
		close (NEXTNUM);
	} 
	if (!(-d "./baskets")) {
		mkdir "./baskets";
	} 
	if (!(-d "./users")) {
		mkdir "./users";
	} 
	if (defined param("currentUser") && param("currentUser") ne "") {
		$user = param("currentUser");
		print hidden(-name=>"currentUser", -value=>"$user");
	}
	our %books = loadValuesToHashTable($bookFile);
}

sub loadValuesToHashTable($) {
	my ($fileName) = @_;
	my %hash = ();
	open(BOOKDB,"$fileName") or die "Cannot open $fileName";
	$readingAuthors = 0;
	while ($line = <BOOKDB>) {
		#if reading authors line by line
		if ($readingAuthors) {
			if ($line =~ m/^\s*\],\s*$/) {
				$readingAuthors = 0;
				$authorsString =~ s/\s*,\s*$//;
				
				if ($authorCount > 2) {
					$authorsString =~ s/,(.*),\s(.*)$/,$1 & $2/;
				} else {
					$authorsString =~ s/,/ &/;
				}
				$hash{$currentISBN}{authors} = $authorsString;
			} elsif ($line =~ m/^\s*"(.*)"\s*/) {
				$authorCount++;
				$authorsString = "$authorsString$1, ";
				$authorsString =~ s/\\(.*)\\/$1/;
			}
		} else {
			#grab the ISBN
			if ($line =~ m/^\s*"(\d+X?)"\s*:\s*{\s*$/) {
				$currentISBN = $1;
			} elsif ($line =~ m/^\s*"authors"\s*:\s*\[\s*$/) {
				$readingAuthors = 1;
				$authorsString = "";
				$authorCount = 0;
			} elsif ($line =~ m/^\s*"(.*)"\s*:\s*"(.*)",\s*$/) {
				#pattern match and pull out all data into a hash table
				$temp = $2;
				$cat = $1;
				$temp =~ s/\\//g;
				$temp =~ s/<[A-Za-z\/]*>//g;
				$hash{$currentISBN}{$cat} = $temp;
			}
		}
	}	
	close(BOOKDB);	
	return %hash;
}

#function preforms a search based on keywords given
sub findData(%@) {
	my $dataRef = shift;
	my %data = %$dataRef;
	my $searchTermRef = shift;
	my @searchTerm = @$searchTermRef;
	
	my %termsByCat = getSearchTerms(@searchTerm);
	my @result = ();
	#go through all books and fields for search
	#if they match, add them to the results table
	foreach $isbn (keys %data) {
		$match = 1;
		foreach $key (keys %termsByCat) {
			if (!exists $data{$isbn}{$key} && $key ne "") {
				print "Unknown keyword\n";
				$match = 0;	
			} else {
				if (!matches($data{$isbn}, $key, $termsByCat{$key})) {
					$match = 0;
				}	
			}
		}
		if ($match) {
			push @result, $isbn;
		}
	}
	return @result;
}

#checks that the given book matches all the keywords given for a field
sub matches(%$@) {
	$bookRef = shift;
	%book = %$bookRef;
	$field = shift;
	$keywordsRef = shift;
	@keywords = @$keywordsRef;
	$matches = 1;
	foreach $word (@keywords) {
		if ($word !~ m/^<.*>$/) {		
			$word =~ s/[\.\*\+\\\{\}\[\]\$\^]+//;
			if ($field eq "") {
				if ($word eq "") {
					$matches=0;
				} elsif (($book{title} !~ m/\b$word\b/i) and ($book{authors} !~ m/\b$word\b/i)) {
					$matches=0;
				}
			} else {
				if ($book{$field} !~ m/\b$word\b/i) {
					$matches=0;
				}
			}
		}
	}
	return $matches;
	
}

#breaks down search terms into fields
#returns an associative array of fields->search terms
sub getSearchTerms(@) {
	%termByCat = ();
	$cat = "";
	@tempArray = ();
	$termByCat{$cat} = \@tempArray;
	foreach $term (@searchTerms) {
		if ($term =~ m/^(.*):(.*)$/i) {
			if (exists $termByCat{$1}) {
				$arrayRef = $termByCat{$1};
				push @$arrayRef, $2;
			} else {
				my @catTerms = ();
				push @catTerms, $2;
				#funky pointer magic to make multiple arrays
				$termByCat{$1} = \@catTerms;
			}
		} else {
			$arrayRef = $termByCat{$cat};
			push @$arrayRef, $term;
		}	
	}
	return %termByCat;
}

sub printBanner() {
	print h1("orinoco.com");
	print "<br><br>\n";
}

sub showLogonPage() {
	print "<table border=\"0\" width=\"200\">\n";
	print "<tr>";
	print "<td width=\"100\">";
	print a("Username:");
	print "</td><td width=\"100\">";
	print textfield(-name=>"username");
	print "<tr>";
	print "<td width=\"100\">";
	print a("Password:");
	print "</td><td width=\"100\">";
	print password_field(-name=>"password");
	print "</table>\n";
	print submit(-name=>"login", -value=>"Login");
	print submit(-name=>"new_account", -value=>"New Account");

}

sub showNewAccountForm() {
	my @textFields = qw(password name street city state postcode email);
	my @fields = ("Password", "Full Name", "Street", "City/Suburb", "State", "Postcode", "Email Address");
	print "<table border=\"0\" width=\"300\">\n";
	$count = 0;
	foreach $title (@fields) {
		print "<tr>";
		print "<td width=\"100\">";
		print a("$title:");
		print "</td><td width=\"100\">";
		if ($title eq "Password") {
			print password_field(-name=>"$fields[$count]");
		} else {
			print textfield(-name=>"$fields[$count]");
		}
		print "</tr>";
		$count++;
	}
	print "</table>";
	print submit(-name=>"newAccountSubmit", -value=>"Create Account");
	print reset(-value=>"Reset Form");

}

sub showSearchBox() {
	print "<table border=0 width=\"400\">";
	print "<tr><td width=\"100\">";
	print a("Search:");
	print "<td>";
	print textfield(-name=>"search");
	print "</table>";
}

sub printListOfBooks(@$) {
	my $arrayRef = shift;
	my @isbns = @$arrayRef;
	my $width = shift;
	print "<table border=\"1\" width=\"$width\">";
	foreach $isbn (@isbns) {
		print "<tr>";
		print "<td>";
		print a($isbn);
		print "</td></tr>";
	}
	print "</table>";
	
}

sub myHashSort {
	#weight non-salesrank items so they end up at the bottom of the list
	if (!(exists $data{$a}{SalesRank})) {
		$data{$a}{SalesRank} = 9999999999999999;
	}
	if (!(exists $data{$b}{SalesRank})) {
		$data{$b}{SalesRank} = 9999999999999999;
	}
	if ($data{$a}{SalesRank} == $data{$b}{SalesRank}) {
		return ($data{$a}{isbn} cmp $data{$b}{isbn});
	} else {
		return ($data{$a}{SalesRank} <=> $data{$b}{SalesRank});
	}
}

sub showSearchResults(@) {
	my $hashref = shift;
	my @data = @$hashref;
	printListOfBooks(\@data, "500");
}

sub processNewAccount() {
	$userName = param("username");
	if (!(-e "./users/$userName")) {
		open (ACCOUNT, "+>./users/$userName") or die "Cannot create new file for user $userName\n";
		my @textFields = qw(password name street city state postcode email);
		foreach $field (@textFields) {
			$line = param($field) . "\n";
			print ACCOUNT "$field=$line";
		}
		close(ACCOUNT);
	} else {
		colorText("$userName already exists.");
		showNewAccountForm();
	}
}

sub checkValidUsername($) {
	my $username = shift;
	if ($username eq "") {
		colorText("Invalid login: logins must be 3-8 characters long.", "red");
		return 0;
	} else {
		chomp $username;
		if ($username =~ m/[^A-Za-z0-9]/) {
			colorText("Invalid login '$username': logins must start with a letter and contain only letters and digits.", "red");
			return 0;
		} elsif (length($username) < 3 || length($username) > 8) {
			colorText ("Invalid login: logins must be 3-8 characters long.", "red");
			return 0;
		} else {
			return 1;
		}
	}
	
}

sub checkValidPassword($) {
	my $password = shift;
	if (length($password) <= 5) {
		colorText("Invalid password: passwords must contain at least 5 characters.", "red");
		return 0;
	} else {
		return 1;
	}
}

sub verifyPassword($$) {
	my $userName = shift;
	my $password = shift;
	if (-e "./users/$userName") {
		open (USER, "./users/$userName") or die "Cannot open user file $userName\n";
		chomp ($line = <USER>);
		$line =~ s/password=//;
		close(USER);
		if ($line eq $password) {
			return 1;
		} else {
			colorText("Invalid password for user '$userName'", "red");
			return 0;
		}
	} else {
		colorText("User '$userName' does not exists.", "red");
		return 0;
	}
}


sub colorText($$) {
	my $message = shift;
	my $color = shift;
	print "<span style=\"color: $color\">$message</span>\n";
}

print header();
print start_html("orinoco.com");
printBanner();
print start_form(-method=>"post", action=>"orinoco.cgi");
initProgram();

if (defined param("login")) {
	if (checkValidUsername(param("username")) && checkValidPassword(param("password")) && verifyPassword(param("username"), param("password"))) {
		$user = param("username");
		print hidden(-name=>"currentUser", -value=>$user);
		showSearchBox();
	} else {
		showLogonPage();
	}
} elsif (defined param("new_account")) {	
	showNewAccountForm();
} elsif (defined param("newAccountSubmit")) {
	if (checkValidPassword(param("password"))) {
		processNewAccount();
	} else {
		showNewAccountForm();
	}
} elsif (defined param("search") && (param("search") =~ m/(.+)/)) {
	@searchTerms = split(' ', param("search"));
	@result = findData(\%books, \@searchTerms);
	showSearchBox();
	showSearchResults(\@result);
	
} else {
	showLogonPage();	
}

print end_form;
print end_html;