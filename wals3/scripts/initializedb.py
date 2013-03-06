from __future__ import unicode_literals
import os
import sys
import transaction
from collections import defaultdict
from itertools import groupby, cycle
import re

from sqlalchemy import engine_from_config, create_engine
from path import path
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from clld.db.meta import (
    DBSession,
    VersionedDBSession,
    Base,
)
from clld.db.models import common
from clld.db.util import compute_language_sources

import wals3
from wals3 import models
from wals3.scripts import uncited


UNCITED_MAP = {}
for k, v in uncited.MAP.items():
    UNCITED_MAP[k.lower()] = v

#DB = 'sqlite:////home/robert/old_projects/legacy/wals_pylons/trunk/wals2/db.sqlite'
DB = create_engine('postgresql://robert@/wals')
REFDB = create_engine('postgresql://robert@/walsrefs')


ABBRS = {
    "A": "agent-like argument",
    "ACCOMP": "accompanied ",
    "ACR": "actor",
    "ACT": "actual",
    "ADEL": "adelative",
    "ADVZ": "adverbializer",
    "AFF": "affirmative",
    "AGT": "agent",
    "ALL": "allative",
    "AN": "action nominal",
    "ANC": "action nominal construction",
    "ANIM": "animate",
    "ANTIP": "antipassive",
    "APPL": "applicative",
    "AS": "asseverative",
    "ASSOC": "associative",
    "ASY": "asymmetric",
    "ATTR": "attributive",
    "AUD": "auditory evidential",
    "AUG": "augmented",
    "C": "common gender",
    "CL": "class (= noun class, gender)",
    "CLF": "classifier",
    "CMPL": "completive",
    "CNTR": "contrary to expectation marker",
    "COLL": "collective",
    "COM": "comitative",
    "COMPR": "comparative",
    "CONN": "connective",
    "CONNEG": "connegative",
    "CONSTR": "construct",
    "CONT": "continuative, continous",
    "CONTEMP": "contemporative",
    "COP": "copula",
    "CPW": "categories per word",
    "CRS": "currently relevant state",
    "DECL": "declarative",
    "DEG": "degree word",
    "DEP": "dependent marker",
    "DES": "desire",
    "DESID": "desiderative",
    "DIM": "diminutive",
    "DIR": "direct",
    "DIR.EVD": "direct evidential",
    "DIRL": "directional",
    "DIST.PST": "distant past",
    "DOBJ": "direct object",
    "DS": "different subject",
    "EMPH": "emphatic",
    "EPENTH": "epenthetic",
    "EPV": "expletive verbal suffix",
    "EVD": "evidential",
    "FACT": "fact",
    "FAM": "familiar",
    "FIN": "finite",
    "FIN.AOR": "finite aorist",
    "FV": "verb-final vowel",
    "HAB": "habitual",
    "HEST": "hesternal past",
    "HHON": "super honorific",
    "HOD": "hodiernal past",
    "HON": "honorific",
    "HORT": "hortative",
    "HUM": "human",
    "IE": "Indo-European",
    "ILL": "illative",
    "IMM.PRET": "immediate preterite",
    "IMM.PST": "immediate past",
    "IMPERS": "impersonal",
    "INAN": "inanimate",
    "INCEP": "inceptive",
    "INCOMPL": "incompletive",
    "IND": "indicative",
    "INDIR.EVD": "indirect evidential",
    "INFER": "inferential evidential",
    "INGR": "ingressive",
    "INTENT": "intentional",
    "INTER": "interrogative",
    "INTF": "intensifier",
    "INTGEN": "intended genitive",
    "INV": "inverse",
    "IO": "indirect object ",
    "IRR": "irrealis",
    "ITER": "iterative",
    "LIG": "ligature",
    "LOCUT": "locutor person marker",
    "MED": "medial",
    "NARR": "narrative",
    "NC": "noun class",
    "NEC": "necessity",
    "NHON": "non-honorific",
    "NOMIN": "nominalization",
    "NON.F": "non-feminine ",
    "NONFIN": "non-finite ",
    "NONFIN.AOR": "non-finite aorist",
    "NP": "noun phrase",
    "NPST": "non-past",
    "NSG": "non-singular",
    "NUM": "numeral",
    "O": "object pronominal marker",
    "OBV": "obviative",
    "OPT": "optative",
    "P": "patient-like argument",
    "PAT": "patient",
    "PATH": "path locative",
    "PCL": "particle",
    "PERS": "personal",
    "PHR.TERM": "phrase terminal marker",
    "PLUPERF": "pluperfect",
    "POS": "possibility",
    "POSTP": "postposition",
    "POT": "potential",
    "PP": "prepositional/postpositional phrase",
    "PRECONTEMP": "precontemporal",
    "PRED": "predicative",
    "PREF": "prefix",
    "PREP": "preposition",
    "PREV": "preverb",
    "PROL": "prolative",
    "PRON": "pronoun",
    "PROP": "proper name",
    "PRTV": "partitive",
    "PST.CONT": "past continuous",
    "PST.PUNCT": "past punctiliar",
    "PSTBEFOREYEST": "past before yesterday (= prehesternal)",
    "PUNCT": "punctual stem",
    "Q": "question-marker",
    "QUOT": "quotative",
    "RDP": "reduplication",
    "REAL": "realis",
    "REC": "recent (past)",
    "RECP": "reciprocal",
    "REM.PST": "remote past",
    "REMOTE": "remote",
    "REPET": "repetitive",
    "RLZ": "realized",
    "RNR": "result nominalizer",
    "S": "sole argument of the intransitive verb",
    "SBJV": "subjunctive",
    "SENS": "sensory evidential",
    "SPEC": "specific",
    "SR": "switch Reference",
    "SS": "same subject",
    "STAT": "stative",
    "SUBORD": "subordination",
    "SUFF": "suffix",
    "SUP": "superessive",
    "SYM": "symmetric",
    "SymAsy": "symmetric and asymmetric",
    "T/A": "tense/ aspect",
    "TD": "time depth/ proximality marker",
    "TELIC": "telic",
    "TEMPRY": "temporary",
    "TH": "thematic suffix",
    "THM": "theme (i.e. the semantic role)",
    "TOD.PST": "today past",
    "TRASL": "traslative",
    "TRI": "trial",
    "UNSP": "unspecified",
    "VBLZ": "verbalizer",
    "VENT": "ventive",
    "VIS": "visual evidential",
    "VP": "verb phrase",
}


class Icons(object):
    filename_pattern = re.compile('(?P<spec>(c|d|s|f|t)[0-9a-f]{3})\.png')

    def __init__(self):
        self._icons = []
        for name in sorted(path(wals3.__file__).dirname().joinpath('static', 'icons').files()):
            m = self.filename_pattern.match(name.splitall()[-1])
            if m:
                self._icons.append(m.group('spec'))

    def __iter__(self):
        return iter(self._icons)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def setup_session(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    VersionedDBSession.configure(bind=engine)


def get_source(id):
    """retrieve a source record from wals_refdb
    """
    res = {'id': id}
    refdb_id = UNCITED_MAP.get(id.lower())
    if not refdb_id:
        for row in REFDB.execute("select id, genre from ref_record, ref_recordofdocument where id = id_r_ref and citekey = '%s'" % id):
            res['genre'] = row['genre']
            refdb_id = row['id']
            break

        if not refdb_id:
            if id[-1] in ['a', 'b', 'c', 'd']:
                refdb_id = UNCITED_MAP.get(id[:-1].lower())
            if not refdb_id:
                return {}

    for row in REFDB.execute("select * from ref_recfields where id_r_ref = %s" % refdb_id):
        res[row['id_name']] = row['id_value']

    authors = ''
    for row in REFDB.execute("select * from ref_recauthors where id_r_ref = %s order by ord" % refdb_id):
        if row['type'] == 'etal':
            authors += ' et al.'
        else:
            if authors:
                authors += ' and '
            authors += row['value']
    res['authors'] = authors

    for row in REFDB.execute("select * from ref_recjournal where id_r_ref = %s" % refdb_id):
        res['journal'] = row['name']
        break

    return res


def main():
    icons = Icons()
    setup_session()
    old_db = DB

    data = defaultdict(dict)

    def add(model, _type, key, **kw):
        new = model(**kw)
        data[_type][key] = new
        DBSession.add(new)
        return new

    missing_sources = []
    with transaction.manager:
        with open('/home/robert/venvs/clld/data/wals-data/missing_source.py', 'w') as fp:
            for row in old_db.execute("select * from reference"):
                try:
                    author, year = row['id'].split('-')
                except:
                    author, year = None, None
                bibdata = get_source(row['id'])
                if not bibdata:
                    fp.write('"%s",\n' % row['id'])
                    missing_sources.append(row['id'])

                kw = {
                    'id': row['id'],
                    'name': row['name'],
                    'description': bibdata.get('title', bibdata.get('booktitle')),
                    'authors': bibdata.get('authors', author),
                    'year': bibdata.get('year', year),
                    'google_book_search_id': row['gbs_id'] or None,
                }
                add(common.Source, 'source', row['id'], **kw)

            #
            # TODO: add additional bibdata as data items
            #

        print('sources missing for %s refs' % len(missing_sources))

        for id, name in ABBRS.items():
            DBSession.add(common.GlossAbbreviation(id=id, name=name))

        for row in old_db.execute("select * from country"):
            add(models.Country, 'country', row['id'], id=row['id'], name=row['name'], continent=row['continent'])

        for row in old_db.execute("select * from family"):
            add(models.Family, 'family', row['id'], id=row['id'], name=row['name'], description=row['comment'])

        for row, icon in zip(list(old_db.execute("select * from genus order by family_id")), cycle(iter(icons))):
            genus = add(models.Genus, 'genus', row['id'], id=row['id'], name=row['name'], icon_id=icon, subfamily=row['subfamily'])
            genus.family = data['family'][row['family_id']]
        DBSession.flush()

        for row in old_db.execute("select * from altname"):
            add(common.Identifier, 'identifier', (row['name'], row['type']),
                name=row['name'], type='name-%s' % row['type'])
        DBSession.flush()

        for row in old_db.execute("select * from isolanguage"):
            add(common.Identifier, 'identifier', row['id'],
                id=row['id'], name=row['name'], type='iso639-3', description=row['dbpedia_url'])
        DBSession.flush()

        for row in old_db.execute("select * from language"):
            kw = dict((key, row[key]) for key in ['id', 'name', 'latitude', 'longitude'])
            lang = add(models.WalsLanguage, 'language', row['id'],
                       samples_100=row['samples_100'] != 0, samples_200=row['samples_200'] != 0, **kw)
            lang.genus = data['genus'][row['genus_id']]

        for row in old_db.execute("select * from author"):
            add(common.Contributor, 'contributor', row['id'], name=row['name'], url=row['www'], id=row['id'], description=row['note'])
        DBSession.flush()

        for row in old_db.execute("select * from country_language"):
            DBSession.add(models.CountryLanguage(
                language=data['language'][row['language_id']],
                country=data['country'][row['country_id']]))

        for row in old_db.execute("select * from altname_language"):
            DBSession.add(common.LanguageIdentifier(
                language=data['language'][row['language_id']],
                identifier=data['identifier'][(row['altname_name'], row['altname_type'])],
                description=row['relation']))
        DBSession.flush()

        for row in old_db.execute("select * from isolanguage_language"):
            DBSession.add(common.LanguageIdentifier(
                language=data['language'][row['language_id']],
                identifier=data['identifier'][row['isolanguage_id']],
                description=row['relation']))
        DBSession.flush()

        for row in old_db.execute("select * from area"):
            add(models.Area, 'area', row['id'], name=row['name'], dbpedia_url=row['dbpedia_url'], id=str(row['id']))
        DBSession.flush()

        for row in old_db.execute("select * from chapter"):
            c = add(models.Chapter, 'contribution', row['id'], id=row['id'], name=row['name'])
            c.area = data['area'][row['area_id']]
        DBSession.flush()

        for row in old_db.execute("select * from feature"):
            param = add(models.Feature, 'parameter', row['id'], id=row['id'], name=row['name'], ordinal_qualifier=row['id'][-1])
            param.chapter = data['contribution'][row['chapter_id']]
        DBSession.flush()

        for row in old_db.execute("select * from value"):
            desc = row['description']
            if desc == 'SOV & NegV/VNeg':
                if row['icon_id'] != 's9ff':
                    desc += ' (a)'
                else:
                    desc += ' (b)'

            domainelement = add(
                models.WalsValue, 'domainelement', (row['feature_id'], row['numeric']),
                id='%s-%s' % (row['feature_id'], row['numeric']),
                name=desc, description=row['long_description'], icon_id=row['icon_id'], numeric=row['numeric'])
            domainelement.parameter = data['parameter'][row['feature_id']]
        DBSession.flush()

        for row in old_db.execute("select * from datapoint"):
            parameter = data['parameter'][row['feature_id']]
            language = data['language'][row['language_id']]
            id_ = '%s-%s' % (parameter.id, language.id)
            value = add(common.Value, 'value', row['id'], id=id_)
            value.language = language
            value.domainelement = data['domainelement'][(row['feature_id'], row['value_numeric'])]
            value.parameter = parameter
            value.contribution = parameter.chapter

        DBSession.flush()

        for row in old_db.execute("select * from datapoint_reference"):
            common.ValueReference(
                value=data['value'][row['datapoint_id']],
                source=data['source'][row['reference_id']],
                description=row['note'],
            )

        for row in old_db.execute("select * from author_chapter"):

            new = common.ContributionContributor(
                ord=row['order'],
                primary=row['primary'] != 0,
                contributor_pk=data['contributor'][row['author_id']].pk,
                contribution_pk=data['contribution'][row['chapter_id']].pk)
            DBSession.add(new)

        lang.name = 'SPECIAL--' + lang.name


def prime_cache():
    #from sqlalchemy.orm import object_mapper

    setup_session()

    with transaction.manager:
        #param = VersionedDBSession.query(common.Parameter).filter(common.Parameter.id == '1A').one()
        #param.description = '%s (%s)' % (param.description, param.version)
        #param.blog_title = '%s (%s)' % (param.description, param.version)
        #
        ##print dir(object_mapper(param).class_)
        ##return
        #domain = list(param.domain)
        #value_map = dict(zip(domain, domain[1:] + domain[:1]))
        #for value in param.values:
        #    value.domainelement = value_map[value.domainelement]
        #return



        # cache number of languages for a parameter:
        for parameter, values in groupby(
            DBSession.query(common.Value).order_by(common.Value.parameter_pk),
            lambda v: v.parameter):

            representation = str(len(set(v.language_pk for v in values)))

            d = None
            for _d in parameter.data:
                if _d.key == 'representation':
                    d = _d
                    break

            if d:
                d.value = representation
            else:
                d = common.Parameter_data(
                    key='representation',
                    value=representation,
                    object_pk=parameter.pk)
                DBSession.add(d)

        compute_language_sources()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main()
    prime_cache()
