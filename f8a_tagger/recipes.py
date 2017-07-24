#!/usr/bin/env python3
"""Keywords extraction/tagging for fabric8-analytics."""

# pylint: disable=no-name-in-module
import daiquiri
from f8a_tagger.keywords_chief import KeywordsChief
from f8a_tagger.parsers import CoreParser
from f8a_tagger.tokenizer import Tokenizer
from f8a_tagger.utils import iter_files
from f8a_tagger.collectors import CollectorBase
import anymarkup
import progressbar

_logger = daiquiri.getLogger(__name__)


def _use_progressbar(iterable, progress=False):
    """Construct progressbar for loops if progressbar requested, otherwise return directly iterable.

    :param iterable: iterable to use
    :param progress: True if print progressbar
    """
    if progress:
        return progressbar.ProgressBar(widgets=[
            progressbar.Timer(), ', ',
            progressbar.Percentage(), ', ',
            progressbar.SimpleProgress(), ', ',
            progressbar.ETA()
        ])(list(iterable))

    return iterable


def lookup(path, keywords_file=None, raw_stopwords_file=None, regexp_stopwords_file=None,
           ignore_errors=False, ngram_size=2, use_progressbar=False):
    # pylint: disable=too-many-arguments
    """Perform keywords lookup.

    :param path:
    :param keywords_file:
    :param raw_stopwords_file:
    :param regexp_stopwords_file:
    :param ignore_errors:
    :param ngram_size:
    :param use_progressbar:
    :return:
    """
    ret = {}

    chief = KeywordsChief(keywords_file)
    if chief.compute_ngram_size() > ngram_size:
        _logger.warning("Computed ngram size (%d) does not reflect supplied ngram size (%d), "
                        "some synonyms will be omitted", chief.compute_ngram_size(), ngram_size)

    for file in _use_progressbar(iter_files(path, ignore_errors), progress=use_progressbar):
        _logger.info("Processing file '%s'", file)
        try:
            content = CoreParser().parse_file(file)
            tokens = Tokenizer(raw_stopwords_file, regexp_stopwords_file, ngram_size).tokenize(content)
            keywords = chief.extract_keywords(tokens)
        except Exception as exc:  # pylint: disable=broad-except
            if not ignore_errors:
                raise
            _logger.exception("Failed to parse content in file '%s': %s", file, str(exc))
            continue

        ret[file] = keywords

    return ret


def collect(collector=None, ignore_errors=False, use_progressbar=False):
    """Collect keywords from external resources.

    :param collector:
    :param ignore_errors:
    :param use_progressbar:
    :return: all collected keywords
    """
    keywords = set()

    for col in (collector or CollectorBase.get_registered_collectors()):
        try:
            collector_instance = CollectorBase.get_collector_class(col)()
            keywords.union(set(collector_instance.execute()))
        except Exception as exc:
            if ignore_errors:
                _logger.exception("Collection of keywords for '%s' failed: %s" % (col, str(exc)))
                continue
            raise

    return list(keywords)


def aggregate(input_keywords_file=None, output_keywords_file=None, no_synonyms=None):
    """Aggregate available topics.

    :param input_keywords_file:
    :param output_keywords_file:
    :param no_synonyms:
    :return:
    """
    pass


def get_registered_collectors():
    """Get all registered collectors."""
    return CollectorBase.get_registered_collectors()