#!/usr/bin/env perl
use warnings;
use strict;
use Data::Dumper;
use Getopt::Long;
use Bio::KBase::Transform::ScriptHelpers qw( parse_input_table parse_excel );
use Bio::KBase::fbaModelServices::ScriptHelpers qw(fbaws get_fba_client runFBACommand universalFBAScriptCode );

my $script = "trns_transform_KBaseFBA.CSV-to-KBaseFBA.FBAModel.pl";

=head1 NAME

$script

=head1 SYNOPSIS

$script --input/-i <Input Excel File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>

=head1 DESCRIPTION

Transform a CSV file into an object in the workspace.

=head1 COMMAND-LINE OPTIONS
$script
	-i --input	name of reactions file with model data
	-o --output     id under which KBaseBiochem.Media is to be saved
	-w --out_ws     workspace where KBaseBiochem.Media is to be saved
	-g --genome	genome for which model was constructed
	-b --biomass	id of biomass reaction in model
	--help          print usage message and exit

=cut

my $In_File   = "";
my $Out_Object = "";
my $Out_WS    = "";
my $Genome    = "Empty";
my $Biomass   = "";
my $Help      = 0;

GetOptions("input|i=s"     => \$In_File,
	   "output|o=s"    => \$Out_Object,
	   "out_ws|w=s"    => \$Out_WS,
	   "genome|g=s"    => \$Genome,
	   "biomass|b=s"   => \$Biomass,
	   "help|h"        => \$Help);

if($Help || !$In_File || !$Out_Object || !$Out_WS){
    print($0." --input/-i <Input Excel File> --output/-o <Output Object ID> --out_ws/-w <Workspace to save Object in> --genome/-g <Input Genome ID> --biomass/-b <Input Biomass ID>\n");
    exit();
}

my $input = {
	model => $Out_Object,
	workspace => $Out_WS,
	genome_workspace => $Out_WS,
	genome => $Genome,
	reactions => [],
	compounds => [],
	biomass => $Biomass,
};
if ($Genome eq "Empty") {
	$input->{genome_workspace} = "PlantSEED" ;
}

my $sheets = parse_excel($In_File);

my $Compound = (grep { $_ =~ /[Cc]ompound/ } keys %$sheets)[0];
my $Reaction = (grep { $_ =~ /[Rr]eaction/ } keys %$sheets)[0];

$input->{reactions} = parse_input_table($sheets->{$Reaction},[
	["id",1],
	["direction",0,"="],
	["compartment",0,"c"],
	["gpr",1],
	["name",0,undef],
	["enzyme",0,undef],
	["pathway",0,undef],
	["reference",0,undef],
	["equation",0,undef],
]);

$input->{compounds} = parse_input_table($sheets->{$Compound},[
	["id",1],
	["charge",0,undef],
	["formula",0,undef],
	["name",1],
	["aliases",0,undef]
]);

foreach my $sheet (keys %$sheets){
    system("rm ".$sheets->{$sheet});
}

my $fba = get_fba_client();

$fba->import_fbamodel($input);

__END__

    Logging:

Log output format
           Datetime in UTC - name of script - log level:
 log message
<YYYY-MM-DDTHH:mm:SS>
 - <script_name> - <level>: <message>

           e.g., 2014-12-10T00:00:00Z - trns_transform_KBaseGenomes.GBK-to-KBaseGenomes.Genome
 - INFO: Validating input file sample.gbff




#1 How many <level> do you plan to support?
#2 What?s the failure report LEVEL? FATAL, FAIL, ???
#3 Do you have any recommended library to use to dump the above format?