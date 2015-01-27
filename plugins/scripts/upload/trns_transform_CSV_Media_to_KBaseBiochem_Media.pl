#!/usr/bin/env perl
#PERL USE
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( parse_input_table  getStderrLogger );
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

=head1 NAME

trns_transform_CSV_Media-to-KBaseBiochem.Media.pl

=head1 SYNOPSIS

trns_transform_CSV_Media-to-KBaseBiochem.Media.pl --input_file_name csv-file --object_name media-id --workspace_name workspace-id

=head1 DESCRIPTION

Transform a CSV file into an object in the workspace.

=head1 COMMAND-LINE OPTIONS
trns_transform_KBaseBiochem.CSV-to-KBaseBiochem.Media.pl --input_file_name --object_name --workspace_name
	-i --input_file_name      csv file
	-o --object_name     id under which KBaseBiochem.Media is to be saved
	-w --workspace_name     workspace where KBaseBiochem.Media is to be saved
	--help          print usage message and exit

=cut

my $logger = getStderrLogger();

my $In_File   = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Help      = 0;

GetOptions("input_file_name|i=s" => \$In_File,
	   "object_name|o=s"     => \$Out_Object,
	   "workspace_name|w=s"  => \$Out_WS,
	   "help|h"              => \$Help);

if($Help || !$In_File || !$Out_Object || !$Out_WS){
    print($0." --input_file_name/-i <Input CSV File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in>\n");
    $logger->warn($0." --input_file_name/-i <Input CSV File> --object_name/-o <Output Object ID> --workspace_name/-w <Workspace to save Object in>\n");
    exit();
}

$logger->info("Data passed = ".join(" | ", ($In_File,$Out_Object,$Out_WS)));

my $mediadata = parse_input_table($In_File,[
	["compounds",1],
	["concentrations",0,"0.001"],
	["minflux",0,"-100"],
	["maxflux",0,"100"],
]);

my $input = {media => $Out_Object,workspace => $Out_WS};
for (my $i=0; $i < @{$mediadata}; $i++) {
	push(@{$input->{compounds}},$mediadata->[$i]->[0]);
	push(@{$input->{maxflux}},$mediadata->[$i]->[3]);
	push(@{$input->{minflux}},$mediadata->[$i]->[2]);
	push(@{$input->{concentrations}},$mediadata->[$i]->[1]);
}

$logger->info("Loading Media WS Object");

use Capture::Tiny qw( capture );
my ($stdout, $stderr, @result) = capture {
    my $fba = get_fba_client();
    $fba->addmedia($input);
};

$logger->info("fbaModelServices addmedia() informational messages\n".$stdout) if $stdout;
$logger->warn("fbaModelServices addmedia() warning messages\n".$stderr) if $stderr;
$logger->info("Loading Media WS Object Complete");
