#! /usr/bin/env perl
#PERL USE
use strict;
use Getopt::Long;
use Try::Tiny;
use JSON;

#KBASE USE
use Bio::KBase::Transform::ScriptHelpers qw( getStderrLogger );

=head1 NAME

trns_transform_OBO_Ontology_to_KBaseOntology_OntologyDictionary.pl

=head1 SYNOPSIS

trns_transform_OBO_Ontology_to_KBaseOntology_OntologyDictionary.pl --input_file_name obo-file --output_file_name ontology-dictionary

=head1 DESCRIPTION

Transform an OBO file into KBaseOntology.OntologyDictionary object

=head1 COMMAND-LINE OPTIONS
trns_transform_OBO_Ontology_to_KBaseOntology_OntologyDictionary.pl --input_file_name --output_file_name
	-i --input_file_name      OBO file
	-o --output_file_name     id under which KBaseOntology.OntologyDictionary is to be saved
        --help                    print usage message and exit

=cut

use File::Basename;
my $Working_Dir=dirname($0);
my $Command = $Working_Dir."/ont.pl";

my ($help, $input, $output);
GetOptions("h|help"      => \$help,
	   "i|input_file_name=s" => \$input,
	   "o|output_file_name=s" => \$output
	  ) or die("Error in command line arguments\n");

my $logger = getStderrLogger();

if($help || !$input || !$output){
    print($0." --input_file_name|-i <Input OBO File> --output_file_name|-o <Output KBaseOntology.OntologyDictionary JSON Flat File>");
    $logger->warn($0." --input_file_name|-i <Input OBO File> --output_file_name|-o <Output KBaseOntology.OntologyDictionary JSON Flat File>");
    exit();
}
$logger->info("Mandatory Data passed = ".join(" | ", ($input,$output)));


try {
    $logger->info("Running OBO transform script");
    system("$Command --from-obo $input > $output")
} catch {
    $logger->warn("Unable to run OBO transform script: $Command --from-obo $input > $output");
    die $_;
};
