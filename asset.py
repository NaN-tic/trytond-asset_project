# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
from sql.aggregate import Max, Sum, Avg

from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, If, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.config import config
DIGITS = int(config.get('digits', 'unit_price_digits', 4))

__all__ = ['ProjectMilestoneGroup', 'ProjectSaleLine', 'Project',
    'ShipmentWork', 'Sale', 'Maintenance', 'MilestoneGroup']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')


class ProjectMilestoneGroup(ModelSQL):
    'Project - Milestone'
    __name__ = 'asset.project-account.invoice.milestone.group'
    _table = 'asset_project_milestone_group_rel'
    project = fields.Many2One('asset.project', 'Project', ondelete='CASCADE',
        required=True, select=True)
    milestone_group = fields.Many2One('account.invoice.milestone.group',
        'Milestone Group',
        ondelete='CASCADE', required=True, select=True)

    @classmethod
    def __setup__(cls):
        super(ProjectMilestoneGroup, cls).__setup__()
        cls._sql_constraints += [
            ('project_unique', 'UNIQUE(project)',
                'The Project must be unique.'),
            ('milestone_group_unique', 'UNIQUE(milestone_group)',
                'The Milestone Group must be unique.'),
            ]


class ProjectSaleLine(ModelSQL, ModelView):
    'Project Sale Line'
    __name__ = 'asset.project.sale.line'
    project = fields.Many2One('asset.project', 'Project', required=True)
    product = fields.Many2One('product.product', 'Product')
    quantity = fields.Float('Quantity',
        digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits'])
    unit = fields.Many2One('product.uom', 'Unit')
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    currency = fields.Many2One('currency.currency', 'Currency')
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    unit_price = fields.Numeric('Unit Price', digits=(16, DIGITS))
    amount = fields.Function(fields.Numeric('Amount',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_amount')

    def get_amount(self, name):
        return self.currency.round(
            Decimal(str(self.quantity)) * self.unit_price)

    @fields.depends('unit')
    def on_change_with_unit_digits(self, name=None):
        if self.unit:
            return self.unit.digits
        return 2

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        return self.currency.digits

    @classmethod
    def table_query(cls):
        pool = Pool()
        Sale = pool.get('sale.sale')
        SaleLine = pool.get('sale.line')
        table = SaleLine.__table__()
        sale = Sale.__table__()

        columns = []
        for name in ('id', 'create_uid', 'write_uid', 'create_date',
                'write_date'):
            columns.append(Max(getattr(table, name)).as_(name))

        columns.extend([sale.project, table.product, sale.currency, table.unit,
                Sum(table.quantity).as_('quantity'),
            Avg(table.unit_price).as_('unit_price')])

        return table.join(sale, condition=(sale.id == table.sale)).select(
            *columns,
            where=((table.type == 'line') &
                (sale.project != None) &
                (sale.state != 'cancel')
                ),
            group_by=(sale.project, sale.currency, table.product, table.unit))


class Project(ModelSQL, ModelView):
    'Asset Project'
    __name__ = 'asset.project'
    _rec_name = 'code'

    company = fields.Many2One('company.company', 'Company', required=True,
        select=True, domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ])
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')
    code = fields.Char('Code', required=True, select=True,
        states={
            'readonly': Eval('code_readonly', True),
            },
        depends=['code_readonly'])
    code_readonly = fields.Function(fields.Boolean('Code Readonly'),
        'get_code_readonly')
    party = fields.Many2One('party.party', 'Party', required=True)
    milestone_group = fields.One2One(
        'asset.project-account.invoice.milestone.group',
        'project', 'milestone_group', 'Milestone Group',
        domain=[
            ('party', '=', Eval('party')),
            ('company', '=', Eval('company')),
            ],
        states={
            'readonly': (Eval('id', 0) > 0) & Bool(Eval('milestone_group', 0)),
            },
        depends=['id', 'party', 'company'])
    milestones = fields.Function(fields.One2Many('account.invoice.milestone',
            None, 'Milestones',
            domain=[
                ('group', '=', Eval('milestone_group')),
                ],
            depends=['milestone_group']),
        'get_milestones', setter='set_milestones')
    asset = fields.Many2One('asset', 'Asset', required=True,
        select=True)
    start_date = fields.Date('Start Date',
        states={
            'invisible': Bool(Eval('maintenance')),
            },
        depends=['maintenance'])
    end_date = fields.Date('End Date',
        states={
            'invisible': Bool(Eval('maintenance')),
            },
        depends=['maintenance'])
    maintenance = fields.Boolean('Maintenance')
    asset_maintenances = fields.One2Many('asset.maintenance', 'reference',
        'Maintenances', size=1)
    category = fields.Function(fields.Many2One('asset.maintenance.category',
            'Category',
            states={
                'required': Bool(Eval('maintenance')),
                'invisible': ~Bool(Eval('maintenance')),
                },
            depends=['maintenance']),
        'get_maintenance', setter='set_maintenance',
        searcher='search_maintenance')
    date_planned = fields.Function(fields.Date('Planned Date',
            states={
                'invisible': ~Bool(Eval('maintenance')),
                },
            depends=['maintenance']),
        'get_maintenance', setter='set_maintenance',
        searcher='search_maintenance')
    date_start = fields.Function(fields.Date('Start Date',
            states={
                'invisible': ~Bool(Eval('maintenance')),
                },
            depends=['maintenance']),
        'get_maintenance', setter='set_maintenance',
        searcher='search_maintenance')
    date_done = fields.Function(fields.Date('Done Date',
            states={
                'invisible': ~Bool(Eval('maintenance')),
                },
            depends=['maintenance']),
        'get_maintenance', setter='set_maintenance',
        searcher='search_maintenance')
    date_next = fields.Function(fields.Date('Next maintenance',
            states={
                'invisible': ~Bool(Eval('maintenance')),
                },
            depends=['maintenance']),
        'get_maintenance', setter='set_maintenance',
        searcher='search_maintenance')

    work_shipments = fields.One2Many('shipment.work', 'project',
        'Shipment Works',
        domain=[
            ('party', '=', Eval('party')),
            ],
        depends=['party'])
    sales = fields.One2Many('sale.sale', 'project', 'Sales',
        domain=[
            ('party', '=', Eval('party', -1)),
            ],
        add_remove=[
            ('state', 'in', ['quotation', 'confirmed', 'processing']),
            ],
        depends=['party'])
    sale_lines = fields.One2Many('asset.project.sale.line', 'project',
        'Sale Lines')
    amount_invoice = fields.Function(fields.Numeric('Amount To Invoice',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_amount_milestones')
    amount_milestones = fields.Function(fields.Numeric('Amount In Milestones',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_amount_milestones')
    amount_to_assign = fields.Function(fields.Numeric('Amount to Assign',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_amount_milestones')
    shipments = fields.Function(fields.One2Many('stock.shipment.out',
            None, 'Shipments'), 'get_shipments')
    shipment_returns = fields.Function(fields.One2Many(
            'stock.shipment.out.return', None, 'Shipment Returns'),
        'get_shipment_returns')
    moves = fields.Function(fields.One2Many('stock.move', None, 'Moves'),
        'get_moves')
    income_labor = fields.Function(fields.Numeric('Income Labor',
        digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_income_labor')
    income_material = fields.Function(fields.Numeric('Income Material',
        digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_income_material')
    income_other = fields.Function(fields.Numeric('Income Other',
        digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_income_other')
    expense_labor = fields.Function(fields.Numeric('Expense Labor',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_expense_labor')
    expense_material = fields.Function(fields.Numeric('Expense Material',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_expense_material')
    expense_other = fields.Function(fields.Numeric('Expense Other',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_expense_other')
    margin_labor = fields.Function(fields.Numeric('Margin Labor',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_margins')
    margin_material = fields.Function(fields.Numeric('Margin Material',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_margins')
    margin_other = fields.Function(fields.Numeric('Margin Other',
            digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
        'get_margins')
    margin_percent_labor = fields.Function(fields.Numeric('Margin(%) Labor',
            digits=(16, 4)),
        'get_margins')
    margin_percent_material = fields.Function(fields.Numeric(
            'Margin (%) Material', digits=(16, 4)),
        'get_margins')
    margin_percent_other = fields.Function(fields.Numeric('Margin (%) Other',
            digits=(16, 4)),
        'get_margins')
    note = fields.Text('Note')

    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_code_readonly():
        Configuration = Pool().get('asset.project.configuration')
        config = Configuration(1)
        return bool(config.project_sequence)

    @fields.depends('company')
    def on_change_with_unit_digits(self, name=None):
        if self.company:
            return self.company.currency.digits
        return 2

    @classmethod
    def get_amount_milestones(self, projects, names):
        res = {}
        for name in names:
            res[name] = dict((p.id, _ZERO) for p in projects)
        for project in projects:
            skip = set()
            for sale in project.sales:
                if not sale.milestone_group or sale.milestone_group.id in skip:
                    continue
                for name, field in [
                        ('amount_milestones', 'amount'),
                        ('amount_to_assign', 'amount_to_assign'),
                        ]:
                    if name in names:
                        res[name][project.id] += getattr(
                            sale.milestone_group, field, _ZERO)
                if 'amount_invoiced' in names:
                    res[name][project.id] += (sale.milestone_group.amount -
                        sale.milestone_group.amount_invoiced)
                skip.add(sale.milestone_group.id)
        return res

    def get_income_labor(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if line.product and line.product.type == 'service':
                    amount += line.amount
        return amount

    def get_income_material(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if line.product and line.product.type != 'service':
                    amount += line.amount
        return amount

    def get_income_other(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if not line.product:
                    amount += line.amount
        return amount

    def get_expense_labor(self, name):
        amount = _ZERO
        for shipment_work in self.work_shipments:
            for line in shipment_work.timesheet_lines:
                amount += line.compute_cost()
        return amount

    def get_expense_material(self, name):
        amount = _ZERO
        for sale in self.sales:
            for line in sale.lines:
                if line.product and line.product.type != 'service':
                    # Compatibility with sale_margin
                    if hasattr(line, 'cost_price'):
                        amount += sale.currency.round(
                            Decimal(str(line.quantity)) * line.cost_price)
                    else:
                        amount += sale.currency.round(line.product.cost_price *
                            Decimal(str(line.quantity)))
        return amount

    def get_expense_other(self, name):
        amount = _ZERO
        return amount

    @classmethod
    def get_margins(cls, projects, names):
        res = {}
        for name in names:
            res[name] = dict((p.id, _ZERO) for p in projects)
        for project in projects:
            for name in names:
                field_name = name.split('_')[-1]
                income = getattr(project, 'income_%s' % field_name)
                expense = getattr(project, 'expense_%s' % field_name)
                if 'percent' in name:
                    if not expense:
                        value = Decimal('1.0')
                    else:
                        value = (income - expense) / expense
                else:
                    value = income - expense
                res[name][project.id] = value
        return res

    def get_code_readonly(self, name):
        return True

    def get_moves(self, name):
        return [m.id for s in self.sales for m in s.moves]

    def get_shipments(self, name):
        return [m.id for s in self.sales for m in s.shipments]

    def get_shipment_returns(self, name):
        return [m.id for s in self.sales for m in s.shipment_returns]

    @classmethod
    def get_maintenance(cls, projects, names):
        pool = Pool()
        Maintenance = pool.get('asset.maintenance')
        res = {}
        for name in names:
            res[name] = dict((m.id, None) for m in projects)

        for maintenance in Maintenance.search([
                    ('reference', 'in', [str(m) for m in projects]),
                    ]):
            project = maintenance.reference.id
            for name in names:
                value = getattr(maintenance, name)
                if isinstance(value, ModelSQL):
                    value = value.id
                res[name][project] = value
        return res

    @classmethod
    def set_maintenance(cls, projects, name, value):
        pool = Pool()
        Maintenance = pool.get('asset.maintenance')
        to_write = []
        to_create = []
        for project in projects:
            if not project.maintenance:
                continue
            if not project.asset_maintenances:
                to_create.append(project.asset_maintenance_vals(
                        {name: value}))
            else:
                to_write.extend(project.asset_maintenances)
        if to_create:
            Maintenance.create(to_create)
        if to_write:
            Maintenance.write(to_write, {
                    name: value,
                    })

    @classmethod
    def search_maintenance(cls, name, clause):
        return [('projects.%s' % name,) + tuple(clause[1:])]

    def asset_maintenance_vals(self, vals):
        'Returns the values for the asset maintenance to be created for self'
        vals['reference'] = str(self)
        vals['asset'] = self.asset.id
        return vals

    def get_milestones(self, name=None):
        return [m.id for m in self.milestone_group.lines]

    @classmethod
    def set_milestones(cls, projects, name, value):
        pool = Pool()
        MilestoneGroup = pool.get('account.invoice.milestone.group')
        groups = [p.milestone_group for p in projects if p.milestone_group]
        if groups:
            MilestoneGroup.write(groups, {
                    'lines': value,
                    })

    @classmethod
    def create(cls, vlist):
        'Fill the reference field with the sale sequence'
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        MilestoneGroup = pool.get('account.invoice.milestone.group')
        Config = pool.get('asset.project.configuration')

        config = Config(1)
        for value in vlist:
            if not value.get('code'):
                code = Sequence.get_id(config.project_sequence.id)
                value['code'] = code
            if not value.get('milestone_group'):
                vals = {'party': value.get('party')}
                group, = MilestoneGroup.create([vals])
                value['milestone_group'] = group.id
        return super(Project, cls).create(vlist)


class ShipmentWork:
    __name__ = 'shipment.work'
    project = fields.Many2One('asset.project', 'Project',
        states={
            'readonly': Eval('state').in_(['checked', 'cancel']),
            },
        depends=['state'])


class Sale:
    __name__ = 'sale.sale'
    project = fields.Many2One('asset.project', 'Project',
        domain=[
            ('party', '=', Eval('party')),
            ],
        depends=['party'])

    @classmethod
    def _ensure_milestone_project_relation(cls, sales):
        to_write = []
        for sale in sales:
            if (sale.project and (not sale.milestone_group or
                        sale.milestone_group != sale.project.milestone_group)):
                to_write.extend(([sale], {
                            'milestone_group': sale.project.milestone_group.id,
                        }))
        if to_write:
            cls.write(*to_write)

    @classmethod
    def create(cls, vlist):
        sales = super(Sale, cls).create(vlist)
        cls._ensure_milestone_project_relation(sales)
        return sales

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        all_sales = []
        for sales, _ in zip(actions, actions):
            all_sales += sales
        super(Sale, cls).write(*args)
        cls._ensure_milestone_project_relation(all_sales)


class Maintenance:
    __name__ = 'asset.maintenance'

    @classmethod
    def _get_reference(cls):
        references = super(Maintenance, cls)._get_reference()
        references.append('asset.project')
        return references


class MilestoneGroup:
    __name__ = 'account.invoice.milestone.group'
    #TODO: Add this to the views
    project = fields.One2One('asset.project-account.invoice.milestone.group',
        'milestone_group', 'project', 'Project', readonly=True,
        domain=[
            ('party', '=', Eval('party')),
            ('company', '=', Eval('company')),
            ],
        depends=['party', 'company'])
