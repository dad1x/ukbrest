from os.path import isdir
import tempfile

from flask import Flask
from flask_restful import Api

from common.genoquery import GenoQuery
from common.pheno2sql import Pheno2SQL
from ukbrest.resources.genotype_apis import GenotypeApiObject
from ukbrest.resources.phenotype_apis import PhenotypeApiObject
from ukbrest.resources.genotype import GenotypePositionsAPI, GenotypeRsidsAPI
from ukbrest.resources.phenotype import PhenotypeFieldsAPI, PhenotypeAPI

app = Flask(__name__)


# Genotype API
genotype_api = GenotypeApiObject(app)

genotype_api.add_resource(
    GenotypePositionsAPI,
    '/ukbrest/api/v1.0/genotype/<int:chr>/positions',
    '/ukbrest/api/v1.0/genotype/<int:chr>/positions/<int:start>',
    '/ukbrest/api/v1.0/genotype/<int:chr>/positions/<int:start>/<int:stop>',
)

genotype_api.add_resource(
    GenotypeRsidsAPI,
    '/ukbrest/api/v1.0/genotype/<int:chr>/rsids',
)

# Phenotype API
phenotype_api = PhenotypeApiObject(app)

phenotype_api.add_resource(
    PhenotypeAPI,
    '/ukbrest/api/v1.0/phenotype',
)

# Phenotype Info API
phenotype_info_api = Api(app, default_mediatype='application/json')

phenotype_api.add_resource(
    PhenotypeFieldsAPI,
    '/ukbrest/api/v1.0/phenotype/fields',
)

if __name__ == '__main__':
    from ipaddress import ip_address
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('genotype_path', type=str, help='UK Biobank genotype (imputed) path')
    parser.add_argument('phenotype_csv', type=str, help='UK Biobank phenotype data in CSV format')
    parser.add_argument('--tmp_dir', dest='tmp_dir', type=str, required=False, help='Directory where write temporal files', default=tempfile.gettempdir())
    parser.add_argument('--db_uri', dest='db_uri', type=str, required=False, help='Database engine URI', default='sqlite:///ukbrest_tmp.db')
    parser.add_argument('--host', dest='host', type=ip_address, required=False, help='Host', default=ip_address('127.0.0.1'))
    parser.add_argument('--port', dest='port', type=int, required=False, help='Port', default=5000)
    parser.add_argument('--debug', dest='debug', action='store_true')

    args = parser.parse_args()

    if not isdir(args.genotype_path):
        raise Exception('Repository path does not exist: {}'.format(args.genotype_path))

    app.config.update({'genoquery': GenoQuery(args.genotype_path, debug=args.debug)})

    csv_file = args.phenotype_csv
    db_engine = args.db_uri
    p2sql = Pheno2SQL(csv_file, db_engine, n_columns_per_table=2, tmpdir=args.tmp_dir)
    p2sql.load_data()

    app.config.update({'pheno2sql': p2sql})

    app.run(host=str(args.host), port=args.port, debug=args.debug)
