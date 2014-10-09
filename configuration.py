# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import Model, ModelSQL, ModelView, ModelSingleton, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['Configuration', 'ConfigurationCompany']
__metaclass__ = PoolMeta


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Project Configuration'
    __name__ = 'asset.project.configuration'
    project_sequence = fields.Function(fields.Many2One(
            'ir.sequence', 'Maintenance Sequence',
            domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'asset.project'),
                ]), 'get_company_config', setter='set_company_config')

    @classmethod
    def get_company_config(self, configs, names):
        pool = Pool()
        CompanyConfig = pool.get('asset.project.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])

        res = {}
        for fname in names:
            res[fname] = {
                configs[0].id: None,
                }
            if company_configs:
                val = getattr(company_configs[0], fname)
                if isinstance(val, Model):
                    val = val.id
                res[fname][configs[0].id] = val
        return res

    @classmethod
    def set_company_config(self, configs, name, value):
        pool = Pool()
        CompanyConfig = pool.get('asset.project.configuration.company')

        company_id = Transaction().context.get('company')
        company_configs = CompanyConfig.search([
                ('company', '=', company_id),
                ])
        if company_configs:
            company_config = company_configs[0]
        else:
            company_config = CompanyConfig(company=company_id)
        setattr(company_config, name, value)
        company_config.save()


class ConfigurationCompany(ModelSQL):
    'Asset Project Configuration per Company'
    __name__ = 'asset.project.configuration.company'

    company = fields.Many2One('company.company', 'Company', required=True,
        ondelete='CASCADE', select=True)
    project_sequence = fields.Many2One('ir.sequence',
        'Project Sequence',
        domain=[
            ('code', '=', 'asset.project'),
            ])
