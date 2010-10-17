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
$basketButton = submit(-name=>"basket", -value=>"Basket");
$ordersButton = submit(-name=>"orders", -value=>"View Orders");
$logOffButton = submit(-name=>"logoff", -value=>"Log Off");
$checkoutButton = submit(-name=>"checkout", -value=>"Checkout");


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
		$currentUser = param("currentUser");
		print hidden(-name=>"currentUser", -value=>"$currentUser");
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
	my %result = ();
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
			$result{$isbn} = $data{$isbn};
		}
	}
	return %result;
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

sub showSearchResults(%) {
	my $hashRef = shift;
	my %hash = %$hashRef;
	foreach $isbn (sort myHashSort keys %hash) {
		push @result, $isbn;
	}
	my @buttonNames = ("Add", "Details");
	printListOfBooks(\@result, "100%", \@buttonNames, 1);
}

sub showConfirmCheckout($) {
	my $error = shift;
	if (-e "./baskets/$currentUser") {
		showBasket();
		print b("Shipping Details");
		print "<br>";
		print "<br>";
		showShippingDetails();
		print $error;
		print "<table>";
		print "<tr>";
		print td(a("Credit Card Number: "));
		print td(textfield(-name=>"creditCardNo"));
		print "</tr>";
		print "<tr>";
		print td(a("Expiry: "));
		print td(textfield(-name=>"creditCardExp"));
		print "</tr>";
		print "</table>";
		my @buttons = ($basketButton, submit(-name=>"finaliseOrder", -value=>"Finalize Order"), $ordersButton, $logOffButton);
		showBottomMenu(\@buttons);
	} else {
		colorText("Your basket is empty", "red");
	}
	
	
}

sub showShippingDetails() {
	open (USER, "./users/$currentUser") or die "Cannot open user file for $currentUser";
	print "Shipping Details:\n";
	foreach $line (<USER>) {
		if ($line =~ m/street=(.*)$/) {
			$street = $1;
		} elsif ($line =~ m/city=(.*)$/) {
			$city = $1;
		} elsif ($line =~ m/state=(.*)$/) {
			$state = $1;
		} elsif ($line =~ m/postcode=(.*)$/) {
			$postcode = $1;
		} elsif ($line =~ m/name=(.*)$/) {
			$name = $1;
		}
	}
	close(USER);
	print "<tt>$name</tt><br>";
	print "<tt>$street</tt><br>";
	print "<tt>$city<tt><br>";
	chomp $state;
	print "<tt>$state, $postcode</tt><br>";
}

sub showBasket() {
	if (-e "./baskets/$currentUser") {
		open (BASKET, "./baskets/$currentUser") or die "Cannot open basket for user $currentUser";
		my @isbns = ();
		foreach $isbn (<BASKET>) {
			chomp $isbn;
			push @isbns, $isbn;
			$books{$isbn}{price} =~ /\$(.*)/;
			$tempNum = $1;
			$totalCost += $tempNum;
		}
		my @buttonNames = qw(Drop Details);
		printListOfBooks(\@isbns, "100%", \@buttonNames, 0);
		print "<tr>";
		print td(b(Total)), td(), td(a($totalCost));
		print "</tr>";
		close (BASKET);
	} else {
		print a("No items in basket");
	}
	
}

sub printListOfBooks(@$@$) {
	my $arrayRef = shift;
	my @isbns = @$arrayRef;
	my $width = shift;
	$arrayRef = shift;
	my @buttonNames = @$arrayRef;
	my $endTable = shift;
	print "<table border=\"1\" width=\"$width\">";
	foreach $isbn (@isbns) {
		print "<tr>";
		if (exists $books{$isbn}{ImageUrlSmall}) {
			print td(img({src=>"$books{$isbn}{ImageUrlSmall}", width=>"$books{$isbn}{SmallImageWidth}", height=>"$books{$isbn}{SmallImageHeight}"}));		
		} else {
			print td();
		}
		print td(i($books{$isbn}{title}), "<br>", a($books{$isbn}{authors}));
		print td("<tt>$books{$isbn}{price}</tt>");
		print "<td>";
		foreach $name (@buttonNames) {
			print submit(-name=>"action $isbn", -value=>$name), "<br>";
		}
		print "</td>";
		print "</tr>";
	}
	print "</table>" if $endTable;
	
}

sub showDetailsISBN(%$) {
	my $bookRef = shift;
	my %book = %$bookRef;
	my $isbn = shift;
	my @dontShow = qw(SmallImageHeight MediumImageHeight LargeImageHeight MediumImageWidth ProductDescription MediumImageUrl ImageUrlMedium ImageUrlSmall ImageUrlLarge SmallImageUrl LargeImageWidth SmallImageWidth LargeImageUrl);
	if (exists $book{ImageUrlLarge}) {
		print img({src=>"$book{ImageUrlLarge}", width=>"$book{LargeImageWidth}", height=>"$book{LargeImageHeight}"});
	}
	print "<table width=\"60%\" border=\"0\">\n";
	foreach $key (sort keys %book) {
		#check if the the key is in the don't show array
		if (!(grep {$_ eq $key} @dontShow)) {
			print "<tr>";
			print td($key), td($book{$key});
			print "</tr>";
		}	
	}
	print "</table>";
	#TODO print buttons down here
}

sub showBottomMenu(@) {
	my $arrayRef = shift;
	my @buttons = @$arrayRef;
	print "<table border\"0\">";
	foreach $button (@buttons) {
		print td($button);
	}
	print "</table>";
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

sub processCheckout($$) {
	$cardNo = shift;
	$expiry = shift;
	if (-e "./orders/NEXT_ORDER_NUMBER") {
		open (NUM, "./orders/NEXT_ORDER_NUMBER") or die "Cannot open the next order number";
		$orderNum = <NUM>;
		chomp $orderNum;
		close(NUM);
	} else {
		$orderNum = 0;
	}
	#create a new file for the order
	open (ORDER_FILE, ">./orders/$orderNum") or die "Cannot create new file $orderNum";
	print ORDER_FILE "order_time=" . time() . "\n";
	print ORDER_FILE "credit_card_number=$cardNo\n";
	print ORDER_FILE "expiry_date=$expiry\n";
	open (BASKET, "./baskets/$currentUser") or die "Cannot open basket for $currentUser";
	foreach $isbn (<BASKET>) {
		if ($isbn ne "") {
			print ORDER_FILE "$isbn";
		}
	}
	close (BASKET);
	close(ORDER_FILE);
	#add the order to the user's record
	open (USER, ">>./orders/$currentUser") or die "Cannot open $currentUser order records";
	print USER "$orderNum\n";
	close (USER);
	$orderNum++;
	#update the next order number
	open (NUM, ">./orders/NEXT_ORDER_NUMBER") or die "Cannot open the next order number";
	print NUM "$orderNum\n";
	close(NUM);
	unlink "./baskets/$currentUser";
}

sub addToBasket($) {
	my $isbn = shift;
	open (BASKET, ">>./baskets/$currentUser") or die "Cannot open basket for $currentUser";
	print BASKET $isbn . "\n";
	close (BASKET);
}

sub dropFromBasket($) {
	my $isbn = shift;
	chomp $isbn;
	if (-e "./baskets/$currentUser") {
		open (BASKET, "./baskets/$currentUser") or die "Cannot open basket for $currentUser";
		@basket = <BASKET>;
		seek BASKET,0,0;
		$found = 0;
		$num = 0;
		foreach $line (<BASKET>) {
			chomp $line;
			if ($line eq $isbn && !$found) {
				$basket[$num] = "";
				$found = 1;
			}
			$num++;
		}
		close (BASKET);
		if ($found) {
			foreach $line (@basket) {
				if ($line ne "") {
					push @newBasket, $line;
				}
			}
			unlink "./baskets/$currentUser";
			if (scalar @newBasket > 0) {
				open (BASKET, ">./baskets/$currentUser");
				foreach $line (@basket) {
					if ($line ne "") {
						print BASKET $line
					}
				}
				close (BASKET);
			}	
		} 
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


sub colorText($$$) {
	my $message = shift;
	my $color = shift;
	my $print = shift;
	my $text = "<span style=\"color: $color\">$message</span>\n";
	print $text unless $print;
	return $text;
}

print header();
print start_html("orinoco.com");
printBanner();
print start_form(-method=>"post", action=>"orinoco.cgi");
initProgram();

@params = param();
foreach $p (@params) {
	if ($p =~ m/^action\s.*$/) {
		$doAction = $p;
	}
}

if (defined param($doAction)){
	$doAction =~ m/^action\s(.*)$/;
	$isbn = $1;
	if (param($doAction) eq "Details") {
		showDetailsISBN($books{$isbn}, $isbn);
	} elsif (param($doAction) eq "Add") {
		addToBasket($isbn);
		@searchTerms = split(' ', param("search"));
		my %result = findData(\%books, \@searchTerms);
		showSearchBox();
		showSearchResults(\%result);
		my @buttons = ($basketButton, $checkoutButton, $ordersButton, $logOffButton);
		showBottomMenu(\@buttons);
	} elsif (param($doAction) eq "Drop") {
		dropFromBasket($isbn);
		showSearchBox();
		showBasket();
		my @buttons = ($basketButton, $checkoutButton, $ordersButton, $logOffButton);
		showBottomMenu(\@buttons);
	}

} elsif (defined param("login") || defined param("basket")) {
	if (checkValidUsername(param("username")) && checkValidPassword(param("password")) && verifyPassword(param("username"), param("password"))) {
		$currentUser = param("username");
		print hidden(-name=>"currentUser", -value=>$currentUser);
		showSearchBox();
		showBasket();
		my @buttons = ($checkoutButton, $ordersButton, $logOffButton);
		showBottomMenu(\@buttons);
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
	my %result = findData(\%books, \@searchTerms);
	showSearchBox();
	showSearchResults(\%result);
	my @buttons = ($basketButton, $checkoutButton, $ordersButton, $logOffButton);
	showBottomMenu(\@buttons);
} else {
	showLogonPage();	
}

print end_form;
print end_html;