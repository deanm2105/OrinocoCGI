#!/usr/bin/perl -w

# Orinoc Stage 3 - CGI Version
# By Dean McGregor

use CGI qw/:all/;

if (@ARGV == 0) {
	use CGI::Carp qw(fatalsToBrowser carpout);
	open(LOG, ">>./warnings") or die "Cannot open errors $!";
	carpout(*LOG);
}

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
		#go to main page
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
} else {
	showLogonPage();	
}

print end_form;
print end_html;