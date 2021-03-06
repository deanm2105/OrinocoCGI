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
$checkoutButton = submit(-name=>"checkout", -value=>"Checkout");
$searchButton = submit(-name=>"searchButton", -value=>"Go!");
$logOffButton = submit(-name=>"logoff", -value=>"Log Off");


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
	if (defined param("currentUser") && param("currentUser") ne "" && !(defined param("logoff"))) {
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
	print "<div id=\"header\">";
	print img({src=>"images/header.jpg", width=>"449", height=>"100"});
	print "</div>";
}

sub showLogonPage() {
	print "<div id=\"login\">";
	print "<table border=\"0\" width=\"250\">\n";
	print "<tr>";
	print "<td width=\"100\">";
	print a("Username:");
	print "</td><td width=\"100\">";
	print textfield(-name=>"username", -style=>"width:95%;");
	print "<tr>";
	print "<td width=\"100\">";
	print a("Password:");
	print "</td><td width=\"100\" align=\"center\">";
	print password_field(-name=>"password", -style=>"width:95%;");
	print "</table>\n";
	print submit(-name=>"login", -value=>"Login");
	print submit(-name=>"new_account", -value=>"New Account");
	print "</div>";
}

sub showNewAccountForm() {
	my @textFields = qw(username password name street city state postcode email);
	my @fields = ("User Name", "Password", "Full Name", "Street", "City/Suburb", "State", "Postcode", "Email Address");
    print "<div id=\"content\">";
	print "<table border=\"0\" width=\"300\">\n";
	$count = 0;
	foreach $title (@fields) {
		print "<tr>";
		print "<td width=\"100\">";
		print a("$title:");
		print "</td><td width=\"100\">";
		if ($title eq "Password") {
			print password_field(-name=>"$textFields[$count]");
		} else {
			print textfield(-name=>"$textFields[$count]");
		}
		print "</tr>";
		$count++;
	}
	print "</table>";
	my @buttons = (submit(-name=>"newAccountSubmit", -value=>"Create Account"), reset(-value=>"Reset Form"));
    showBottomMenu(\@buttons);
    print "</div>";
}

sub showSearchBox() {
	print "<div class=\"topMenu\">";
	print "<table border=0 width=\"450\" id=\"searchTable\">";
	print "<tr><td align=\"right\">";
	print b("Search:");
	print "<td>";
	print textfield(-name=>"search", style=>"width:260px;");
	print $searchButton;
	print "</table>";
	print "</div>";
	print "<div class=\"topMenu\" style=\"text-align:right\">";
    print b("Currently logged in as: '$currentUser'");
    print $logOffButton;
    print "</div>";
}

sub showSearchResults(%) {
	my $hashRef = shift;
	%data = %$hashRef;
	$numKeys = keys %data;
    print "<div id=\"content\">";
	if ($numKeys == 0) {
		colorText("No books matched", "red");
	} else {
		foreach $isbn (sort bySalesRank %data) {
            print STDERR "$data{$isbn}{SalesRank}\n";
			push @result, $isbn;
		}
	}
	my @buttonNames = ("Add", "Details");
	printListOfBooks(\@result, "100%", \@buttonNames, 1);
    print "</div>";
    sub bySalesRank {
		my $max_sales_rank = 100000000;
		my $s1 = $data{$a}{SalesRank} || $max_sales_rank;
		my $s2 = $data{$b}{SalesRank} || $max_sales_rank;
		return $a cmp $b if $s1 == $s2;
		return $s1 <=> $s2;
	}
    
}


sub showConfirmCheckout($) {
	my $error = shift;
    showSearchBox();
    print "<div id=\"content\">";
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
	    my @buttons = ($basketButton, $ordersButton, $logOffButton);
	    showBottomMenu(\@buttons);
	}	
    print "</div>";	
}

sub showMainPage() {
	showSearchBox();
    print "<div id=\"content\">";
	showBasket();
	my @buttons = ($checkoutButton, $ordersButton, $logOffButton);
	showBottomMenu(\@buttons);
    print "</div>";
}

sub showShippingDetails() {
	open (USER, "./users/$currentUser") or die "Cannot open user file for $currentUser";
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
		print "<div id=\"basketMessage\">";
		print b("Basket:"), "<br>";
		print "</div>";
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
		printListOfBooks(\@isbns, "80%", \@buttonNames, 0);
		print "<tr>";
		$priceString = sprintf("\$%.2f", $totalCost);
		print td(b(Total)), td(), td("<tt>$priceString</tt>");
		print "</tr>";
		print "</table>";
		close (BASKET);
	} else {
		print "<div id=\"basketMessage\">";
		print a("No items in basket");
		print "</div>";
	}
	
}

sub viewOrders() {
	if (!(-e "./orders/$currentUser")) {
        showSearchBox();
        print "<div id=\"content\">";
		colorText("No orders for $currentUser", "red");
	} else {
        showSearchBox();
        print "<div id=\"content\">";
		open (ORDERS, "./orders/$currentUser") or die ("Cannot open orders file for $currentUser");
		foreach $number (<ORDERS>) {
			chomp $number;
			printOrderDetails($number);
		}
		close (ORDERS);
		print "<br>";
	}
    print "</div>";
}

sub printOrderDetails($) {
	my $number = shift;
	open (CURRENT_ORDER, "./orders/$number") or die "Cannot open order number $number";
	$line = <CURRENT_ORDER>;
	$line =~ /.*=(.*)/;
	$time = $1;
	chomp $time;
	$timeStr = localtime ($time);
	print "<table border=\"0\">";
	print "<tr>";
	print td(a("Order #$number - $timeStr")), "<br>";
	$line = <CURRENT_ORDER>;
	$line =~ /.*=(.*)/;
	$cardNo = $1;
	$line = <CURRENT_ORDER>;
	$line =~ /.*=(.*)/;
	$expiry = $1;
	chomp $cardNo;
	chomp $expiry;
	print "<tr>";
	print td(a("Credit Card Number: $cardNo (Expiry $expiry)")), "<br>";
	print "<tr>";
    my @isbns = ();
	my $totalCost = 0;
	while ($line = <CURRENT_ORDER>) {
		chomp $line;
		push @isbns, $line;
		$books{$line}{price} =~ /\$(.*)/;
		$tempNum = $1;
		$totalCost += $tempNum;
	}
	printListOfBooks(\@isbns, "60%", (), 0);
	print "<tr>";
	$priceString = sprintf("\$%.2f", $totalCost);
	print td(b(Total)), td(), td("<tt>$priceString</tt>");
	print "</tr>";
	print "</table>";
	close (CURRENT_ORDER);
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
		if (scalar @buttonNames > 0) {
			print "<td>";
			foreach $name (@buttonNames) {
				print submit(-name=>"action $isbn", -value=>$name), "<br>";
			}
			print "</td>";	
		}
		print "</tr>";
	}
	print "</table>" if $endTable;
	
}

sub showDetailsISBN(%$) {
	my $bookRef = shift;
	my %book = %$bookRef;
	my $isbn = shift;
	my @dontShow = qw(SmallImageHeight MediumImageHeight LargeImageHeight MediumImageWidth ProductDescription MediumImageUrl ImageUrlMedium ImageUrlSmall ImageUrlLarge SmallImageUrl LargeImageWidth SmallImageWidth LargeImageUrl);
    showSearchBox();
    print "<div id=\"content\">";
	print "<table width=\"60%\" border=\"0\" align=\"center\">\n";
	if (exists $book{ImageUrlLarge}) {
		print "<tr><td colspan=\"2\" align=\"center\">";
		print "<div id=\"bookImage\">";
		print img({src=>"$book{ImageUrlLarge}", width=>"$book{LargeImageWidth}", height=>"$book{LargeImageHeight}"});
		print "</div>";
		print "</td></tr>";
		
	}
	foreach $key (sort keys %book) {
		#check if the the key is in the don't show array
		if (!(grep {$_ eq $key} @dontShow)) {
			print "<tr>";
			print td($key), td($book{$key});
			print "</tr>";
		}	
	}
	print "</table>";
	print hidden(-name=>"currentPage", -value=>"details $isbn");
	my @buttons = ($basketButton, submit(-name=>"action $isbn", -value=>"Add"), $checkoutButton, $ordersButton, $logOffButton);
	showBottomMenu(\@buttons);
    print "</div>";
}

sub showBottomMenu(@) {
	my $arrayRef = shift;
	my @buttons = @$arrayRef;
	print "<table border=\"0\">";
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
	if (length($password) < 5) {
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

#checks a valid credit card number is a string of 16 digits
sub validateCreditCard($) {
	my $cardNo = shift;
	chomp $cardNo;
	if (length($cardNo) == 16) {
		if ($cardNo !~ m/[0-9]{16}/) {
			colorText("Invalid credit card number - must be 16 digits.", "red");
			return 0;
		}
	} else {
		colorText("Invalid credit card number - must be 16 digits.", "red");
		return 0;
	}
	return 1;
}

#checks the formatting of the expiry is mm/yy
sub checkExpiry($) {
	my $expiry = shift;
	chomp $expiry;
	if ($expiry !~ m/[0-9]{2}\/[0-9]{2}/) {
		colorText("Invalid expiry date - must be mm/yy, e.g. 11/04.", "red");
		return 0;
	}
	return 1;
}

sub checkUserExists($) {
	my $user = shift;
	if ((-e "./users/$user")) {
		colorText("'$user' already exists.", "red");
	}
	return (-e "./users/$user");
}

sub colorText($$$) {
	my $message = shift;
	my $color = shift;
	my $print = shift;
	my $text = "<div class=\"errorText\">\n\t<span style=\"color: $color\">$message</span>\n</div>";
	print $text unless $print;
	return $text;
}

print header();
print start_html(-title=>"orinoco.com", 
				-style => { -src => "main.css",
                             -type => "text/css",
                           },);
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
		if (defined param("currentPage")) {
			$temp = param("currentPage");
			$temp = /details\s(.*)/;
			$newIsbn = $1;
			showDetailsISBN($books{$newIsbn}, $newIsbn);
		} else {
			@searchTerms = split(' ', param("search"));
			my %result = findData(\%books, \@searchTerms);
			showSearchBox();
			showSearchResults(\%result);
			my @buttons = ($basketButton, $checkoutButton, $ordersButton, $logOffButton);
			showBottomMenu(\@buttons);
		}
	} elsif (param($doAction) eq "Drop") {
		dropFromBasket($isbn);
		showSearchBox();
		showBasket();
		my @buttons = ($basketButton, $checkoutButton, $ordersButton, $logOffButton);
		showBottomMenu(\@buttons);
	}

} elsif (defined param("login")) {
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
} elsif (defined param("basket")) {
	showMainPage();
} elsif (defined param("checkout")) {
	showConfirmCheckout(0);
} elsif (defined param("new_account")) {	
	showNewAccountForm();
} elsif (defined param("newAccountSubmit")) {
	if (checkValidPassword(param("password")) && !checkUserExists(param("username")) && checkValidUsername(param("username"))) {
		processNewAccount();
		$currentUser = param("username");
		print hidden(-name=>"currentUser", -value=>$currentUser);
		showMainPage();
	} else {
		showNewAccountForm();
	}	
} elsif (defined param("finaliseOrder")) {
	if (validateCreditCard(param("creditCardNo")) && checkExpiry(param("creditCardExp"))) {
		processCheckout(param("creditCardNo"), param("creditCardExp"));
		showMainPage();
	} else {
		showConfirmCheckout(0);
	}
} elsif (defined param("orders")) {
	viewOrders();
	my @buttons = ($basketButton, $checkoutButton, $logOffButton);
    showBottomMenu(\@buttons);
} elsif (defined param("logoff")) {
	colorText ("Sucessfully logged out.", "green", "");
	showLogonPage();
} elsif ((defined param("search") && (param("search") =~ m/(.+)/)) || defined param("searchButton")) {
	@searchTerms = split(' ', param("search"));
	my %result = findData(\%books, \@searchTerms);
	showSearchBox();
    if (scalar @searchTerms > 0) {
        showSearchResults(\%result);
    } else {
        colorText("No search terms entered!", "red", "");
    }
    my @buttons = ($basketButton, $checkoutButton, $ordersButton, $logOffButton);
    showBottomMenu(\@buttons);
} else {
	showLogonPage();	
}

print end_form;
print end_html;
