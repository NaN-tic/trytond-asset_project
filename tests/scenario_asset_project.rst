============================
Asset Project Scenario
============================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install sale::

    >>> Module = Model.get('ir.module.module')
    >>> sale_module, = Module.find([('name', '=', 'asset_project')])
    >>> Module.install([sale_module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name=str(today.year))
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_seq = Sequence(name=str(today.year), code='account.move',
    ...     company=company)
    >>> post_move_seq.save()
    >>> fiscalyear.post_move_sequence = post_move_seq
    >>> invoice_seq = SequenceStrict(name=str(today.year),
    ...     code='account.invoice', company=company)
    >>> invoice_seq.save()
    >>> fiscalyear.out_invoice_sequence = invoice_seq
    >>> fiscalyear.in_invoice_sequence = invoice_seq
    >>> fiscalyear.out_credit_note_sequence = invoice_seq
    >>> fiscalyear.in_credit_note_sequence = invoice_seq
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> Journal = Model.get('account.journal')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> revenue, = Account.find([
    ...         ('kind', '=', 'revenue'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')
    >>> cash, = Account.find([
    ...         ('kind', '=', 'other'),
    ...         ('name', '=', 'Main Cash'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> cash_journal, = Journal.find([('type', '=', 'cash')])
    >>> cash_journal.credit_account = cash
    >>> cash_journal.debit_account = cash
    >>> cash_journal.save()

Create Employee::

    >>> Employee = Model.get('company.employee')
    >>> party = Party(name='Employee')
    >>> party.save()
    >>> employee = Employee()
    >>> employee.party = party
    >>> employee.company = company
    >>> cost = employee.cost_prices.new()
    >>> cost.date = today
    >>> cost.cost_price = Decimal('10.0')
    >>> employee.save()
    >>> user, = User.find([])
    >>> user.employees.append(employee)
    >>> user.employee = employee
    >>> user.save()
    >>> config._context = User.get_preferences(True, config.context)

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> category = ProductCategory(name='Category')
    >>> category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.category = category
    >>> template.default_uom = unit
    >>> template.type = 'assets'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('8')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> product.template = template
    >>> product.save()

    >>> service = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.salable = True
    >>> template.list_price = Decimal('30')
    >>> template.cost_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> template.account_expense = expense
    >>> template.account_revenue = revenue
    >>> template.save()
    >>> service.template = template
    >>> service.save()

Create payment term::

    >>> PaymentTerm = Model.get('account.invoice.payment_term')
    >>> PaymentTermLine = Model.get('account.invoice.payment_term.line')
    >>> payment_term = PaymentTerm(name='Direct')
    >>> payment_term_line = PaymentTermLine(type='remainder', days=0)
    >>> payment_term.lines.append(payment_term_line)
    >>> payment_term.save()

Create an asset::

    >>> Asset = Model.get('asset')
    >>> asset = Asset()
    >>> asset.name = 'Asset'
    >>> asset.product = product
    >>> asset.save()

Create a Sale::

    >>> Sale = Model.get('sale.sale')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = product
    >>> sale_line.quantity = 10
    >>> sale_line = sale.lines.new()
    >>> sale_line.product = service
    >>> sale_line.quantity = 5
    >>> sale_line = sale.lines.new()
    >>> sale_line.description = 'Taxes'
    >>> sale_line.quantity = 1
    >>> sale_line.unit_price = Decimal('15.0')
    >>> sale.save()

Create a Project::

    >>> Project = Model.get('asset.project')
    >>> project = Project()
    >>> project.code = 'MAIN'
    >>> project.party = customer
    >>> project.asset = asset
    >>> project.sales.append(sale)
    >>> project.save()
    >>> project.income_labor
    Decimal('150.00')
    >>> project.income_material
    Decimal('100.00')
    >>> project.income_other
    Decimal('15.00')
    >>> project.expense_material
    Decimal('80.00')
    >>> project.expense_labor
    Decimal('0.0')
    >>> project.expense_other
    Decimal('0.0')
    >>> project.margin_labor
    Decimal('150.00')
    >>> project.margin_percent_labor
    Decimal('1.0')
    >>> project.margin_material
    Decimal('20.00')
    >>> project.margin_percent_material
    Decimal('0.25')
    >>> project.margin_other
    Decimal('15.00')
    >>> project.margin_percent_other
    Decimal('1.0')

Create a milestone and confirm the sale::

    >>> MileStoneGroup = Model.get('account.invoice.milestone.group')
    >>> SaleLine = Model.get('sale.line')
    >>> group = MileStoneGroup(party=customer)
    >>> first_milestone = group.lines.new()
    >>> first_milestone.invoice_method = 'amount'
    >>> first_milestone.trigger = 'manual'
    >>> first_milestone.amount = Decimal('150.0')
    >>> product_line  = SaleLine(sale.lines[0].id)
    >>> first_milestone.trigger_lines.append(product_line)
    >>> second_milestone = group.lines.new()
    >>> second_milestone.invoice_method = 'amount'
    >>> second_milestone.trigger = 'manual'
    >>> second_milestone.amount = Decimal('100.0')
    >>> service_line  = SaleLine(sale.lines[1].id)
    >>> second_milestone.trigger_lines.append(service_line)
    >>> group.save()
    >>> sale.milestone_group = group
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> project.reload()
    >>> project.amount_to_assign
    Decimal('265.00')
    >>> project.amount_milestones
    Decimal('265.00')

Create a shipment work and check that the cost is updated::

    >>> shipment = project.work_shipments.new()
    >>> shipment.work_name = 'Work'
    >>> shipment.work_description = 'Work'
    >>> shipment.party = customer
    >>> project.save()
    >>> project.reload()
    >>> shipment, = project.work_shipments
    >>> shipment.click('pending')
    >>> shipment.planned_date = today
    >>> shipment.click('plan')
    >>> shipment.done_description = 'Done'
    >>> shipment.click('done')
    >>> timesheet = shipment.timesheet_lines.new()
    >>> timesheet.employee = employee
    >>> timesheet.hours = 3.0
    >>> shipment.save()
    >>> project.reload()
    >>> project.expense_labor
    Decimal('30.00')
    >>> project.margin_labor
    Decimal('120.00')
    >>> project.margin_percent_labor
    Decimal('4')
