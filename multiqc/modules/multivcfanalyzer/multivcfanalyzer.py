#!/usr/bin/env python

""" MultiQC module to parse output from MultiVCFAnalyzer """

from __future__ import print_function
from collections import OrderedDict
import logging
import json

from multiqc.plots import bargraph
from multiqc.modules.base_module import BaseMultiqcModule

# Initialise the logger
log = logging.getLogger(__name__)

class MultiqcModule(BaseMultiqcModule):
    """ MultiVCFAnalyzer module """

    def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='MultiVCFAnalyzer', anchor='multivcfanalyzer',
        href="https://github.com/alexherbig/MultiVCFAnalyzer",
        info="""MultiVCFAnalyzer reads multiple VCF files as produced by the GATK UnifiedGenotyper and after filtering provides the combined genotype calls in a number of formats that are suitable for follow-up analyses such as phylogenetic reconstruction, SNP effect analyses, population genetic analyses etc.""")

        # Find and load any MultiVCFAnalyzer reports
        self.mvcf_data = dict()

        # Find and load JSON file
        for f in self.find_log_files('multivcfanalyzer', filehandles=True):
            self.parse_data(f)

        # Filter samples
        self.mvcf_data = self.ignore_samples(self.mvcf_data)

        # Return if no samples found
        if len(self.mvcf_data) == 0:
            raise UserWarning

        # Save data output file
        self.write_data_file(self.mvcf_data, 'multiqc_multivcfanalyzer_metrics')

        # Add to General Statistics
        self.addSummaryMetrics()

        # Plots
        self.read_count_barplot()
        self.snp_count_barplot()

    def parse_data(self, f):
        try:
            data = json.load(f['f'])
        except Exception as e:
            log.debug(e)
            log.warn("Could not parse MultiVCFAnalyzer JSON: '{}'".format(f['fn']))
            return

        # Parse JSON data to a dict
        for s_name in data:
            if (s_name == 'metadata'):
                continue

            s_clean = self.clean_s_name(s_name, f['root'])
            if s_clean in self.mvcf_data:
                log.debug("Duplicate sample name found! Overwriting: {}".format(s_clean))

            self.add_data_source(f, s_clean)
            self.mvcf_data[s_clean] = dict()

            for k, v in data[s_name].items():
                try:
                    self.mvcf_data[s_clean][k] = float(v)
                except ValueError:
                    self.mvcf_data[s_clean][k] = v

    def addSummaryMetrics(self):
        """ Take the parsed stats from SexDetErrmine and add it to the main plot """

        headers = OrderedDict()
        headers['SNP Calls (all)'] = {
            'title': 'All SNP calls',
            'description': 'The complete set of SNP calls',
            'scale': 'OrRd',
            'hidden': True,
            'shared_key': 'snp_call'
        }
        headers['SNP Calls (het)'] = {
            'title': 'Heterozygous SNP Calls',
            'description': 'The set of heterozygous SNP calls',
            'scale': 'OrRd',
            'hidden': True,
            'shared_key': 'snp_call'
        }
        headers['coverage(fold)'] = {
            'title': 'Fold Coverage',
            'description': 'The fold coverage on average over all positions.',
            'scale': 'OrRd',
            'hidden': True,
            'shared_key': 'coverage'
        }
        headers['coverage(percent)'] = {
            'title': 'Percent Covered',
            'description': 'Percentage of genome covered by selected coverage threshold.',
            'scale': 'PuBuGn',
            'shared_key': 'coverage'
        }
        headers['refCall'] = {
            'title': 'Number of reference calls',
            'description': 'Number of calls where there is a reference allele.',
            'scale': 'BuPu',
            'shared_key': 'calls'
        }
        headers['allPos'] = {
            'title': 'XXXX',
            'description': 'YYYY',
            'scale': 'BuPu',
            'shared_key': 'calls'
        }
        headers['noCall'] = {
            'title': 'XXXX',
            'description': 'YYYY',
            'scale': 'BuPu',
            'shared_key': 'calls'
        }
        headers['discardedRefCall'] = {
            'title': 'XXXX',
            'description': 'YYYY',
            'scale': 'BuPu',
            'shared_key': 'snp_ccallsount'
        }
        headers['discardedVarCall'] = {
            'title': 'XXXX',
            'description': 'YYYYY',
            'scale': 'BuPu',
            'shared_key': 'calls'
        }
        headers['filteredVarCall'] = {
            'title': 'XXXXX',
            'description': 'YYYYY',
            'scale': 'BuPu',
            'shared_key': 'calls'
        }
        headers['unhandledGenotype'] = {
            'title': 'An unhandled genotype',
            'description': 'A genotype that can\'t be used by MultiVCFAnalyzer.',
            'scale': 'BuPu',
            'shared_key': 'snp_count'
        }

        self.general_stats_addcols(self.mvcf_data, headers)

    def read_count_barplot(self):
        """ Make a bar plot showing numbers for individual call classes.
        """
        cats = OrderedDict()
        cats['NR Aut'] = { 'name': 'Autosomal Reads' }
        cats['NrX'] = { 'name': 'Reads on X' }
        cats['NrY'] = { 'name': 'Reads on Y' }

        config = {
            'id': 'sexdeterrmine-readcounts-plot',
            'title': 'SexDetErrmine: Read Counts',
            'ylab': '# Reads'
        }

        self.add_section(
            name = 'Read Counts',
            anchor = 'sexdeterrmine-readcounts',
            description = 'The number of reads covering positions on the autosomes, X and Y chromosomes.',
            plot = bargraph.plot(self.mvcf_data, cats, config)
        )

    def snp_count_barplot(self):
        """ Make a bar plot showing read counts on Autosomal, X and Y chr
        """
        cats = OrderedDict()
        cats['Snps Autosomal'] = { 'name': 'Autosomal SNPs' }
        cats['XSnps'] = { 'name': 'SNPs on X' }
        cats['YSnps'] = { 'name': 'SNPs on Y' }

        config = {
            'id': 'sexdeterrmine-snps-plot',
            'title': 'SexDetErrmine: SNP Counts',
            'ylab': '# Reads'
        }

        self.add_section(
            name = 'SNP Counts',
            anchor = 'sexdeterrmine-snps',
            description = 'Total number of SNP positions. When supplied with a BED file, this includes only positions specified there.',
            plot = bargraph.plot(self.mvcf_data, cats, config)
        )
