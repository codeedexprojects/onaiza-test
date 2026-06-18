from versatileimagefield.fields import VersatileImageField
from main.models import BaseModel
import uuid
from django.utils import timezone
from decimal import Decimal
from model_utils import Choices
''''''
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
''''''

ACCOUNTHEAD_TYPES = Choices(
    (10, 'asset', 'Asset'),
    (15, 'liability', 'Liability'),
    (20, 'expense', 'Expense'),
    (25, 'income', 'Income')
)
OPENING_TYPE = (
    ('debit', 'Debit'),
    ('credit', 'Credit')
)

BANK_ACCOUNT_TYPE = Choices(
    ('savings', 'Savings'),
    ('current', 'Current'),
)

PAYMENTVOUCHER_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
PAYMENTVOUCHER_TRANSFER_TYPES = Choices(
    (10, 'cash', 'Cash'),
    (15, 'cheque', 'Cheque'),
    (20, 'draft', 'Draft'),
    (25, 'bank_transfer', 'Bank Transfer'),
    (30, 'credit', 'Credit')
)
RECEIPTVOUCHER_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
RECEIPTVOUCHER_TRANSFER_TYPES = Choices(
    (10, 'cash', 'Cash'),
    (15, 'cheque', 'Cheque'),
    (20, 'draft', 'Draft'),
    (25, 'bank_transfer', 'Bank Transfer'),
    (30, 'credit', 'Credit')
)
JOURNALVOUCHERITEM_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
SUBLEDGEROPENING_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
SUBLEDGEROPENING_SUB_LEDGER_TYPES = Choices(
    (10, 'customer', 'Customer'),
    (20, 'supplier', 'Supplier'),
    (30, 'vendor', 'Vendor'),
    (40, 'delivery_agent', 'Delivery Agent'),
)
ACCOUNTHEADPENING_AMOUNT_TYPES = Choices(
    ('credit', 'Credit'),
    ('debit', 'Debit')
)
FINANCIALSUBLEDGEROPENING_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
CREDITNOTE_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
CREDITNOTE_TRANSFER_TYPES = Choices(
    (10, 'cash', 'Cash'),
    (15, 'cheque', 'Cheque'),
    (20, 'draft', 'Draft'),
    (25, 'bank_transfer', 'Bank Transfer'),
    # (30, 'credit', 'Credit')
)
DEBITNOTE_AMOUNT_TYPES = Choices(
    (10, 'credit', 'Credit'),
    (20, 'debit', 'Debit')
)
DEBITNOTE_TRANSFER_TYPES = Choices(
    (10, 'cash', 'Cash'),
    (15, 'cheque', 'Cheque'),
    (20, 'draft', 'Draft'),
    (25, 'bank_transfer', 'Bank Transfer'),
    # (30, 'credit', 'Credit')
)
PAYMENTVOUCHER_CHEQUE_STATUS = Choices(
    (10, 'cleared', 'Cleared'),
    (15, 'cheque_bounce', 'Cheque Bounce'),
    (20, 'pending', 'Pending')
)
RECEIPTVOUCHER_CHEQUE_STATUS = Choices(
    (10, 'cleared', 'Cleared'),
    (15, 'cheque_bounce', 'Cheque Bounce'),
    (20, 'pending', 'Pending')
)
DEBITNOTE_CHEQUE_STATUS = Choices(
    (10, 'cleared', 'Cleared'),
    (15, 'cheque_bounce', 'Cheque Bounce'),
    (20, 'pending', 'Pending')
)
CREDITNOTE_CHEQUE_STATUS = Choices(
    (10, 'cleared', 'Cleared'),
    (15, 'cheque_bounce', 'Cheque Bounce'),
    (20, 'pending', 'Pending')
)

class FinancialYear(BaseModel):
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'finance_financial_year'
        verbose_name = _('Financial Year')
        verbose_name_plural = _('Financial Years')
        ordering = ('-start_date',)

    def __str__(self):
        return str(self.start_date)


class InvoicePrefix(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    whole_sale = models.CharField(max_length=128)
    retail_sale = models.CharField(max_length=128)
    order = models.CharField(max_length=128)
    purchase = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'invoic_prefix'
        verbose_name = _('Invoice Prefix')
        verbose_name_plural = _('Invoice Prefixs')
        ordering = ('purchase',)

    def __str__(self):
        return self.purchase


class AccountGroup(models.Model):
    creator = models.ForeignKey("auth.User", blank=True, null=True, default=1, related_name="creator_%(class)s_objects", on_delete=models.CASCADE)
    updater = models.ForeignKey("auth.User", blank=True, null=True, default=1, related_name="updater_%(class)s_objects", on_delete=models.CASCADE)
    date_added = models.DateTimeField(db_index=True, blank=True, null=True, default=timezone.now)
    date_updated = models.DateTimeField(blank=True, null=True, default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    group_type = models.IntegerField(choices=ACCOUNTHEAD_TYPES)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128, blank=True, null=True)
    deleted_reason = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'finance_account_group'
        verbose_name = _('Account Group')
        verbose_name_plural = _('Account Groups')
        ordering = ('name',)

    def __str__(self):
        return self.name


class AccountHead(models.Model):
    creator = models.ForeignKey("auth.User", blank=True, null=True, default=1, related_name="creator_%(class)s_objects", on_delete=models.CASCADE)
    updater = models.ForeignKey("auth.User", blank=True, null=True, default=1, related_name="updater_%(class)s_objects", on_delete=models.CASCADE)
    date_added = models.DateTimeField(db_index=True, blank=True, null=True, default=timezone.now)
    date_updated = models.DateTimeField(blank=True, null=True, default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    name = models.CharField(max_length=128)
    code = models.CharField(max_length=128, blank=True, null=True)
    account_group = models.ForeignKey('finance.AccountGroup', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    bank_account = models.ForeignKey('finance.BankAccount', limit_choices_to={'is_deleted': False}, blank=True, null=True, on_delete=models.CASCADE)
    deleted_reason = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'finance_account_head'
        verbose_name = _('Account Head')
        verbose_name_plural = _('Account Heads')
        ordering = ('name',)

    def __str__(self):

        return self.name


class BankAccount(BaseModel):
    warehouse = models.ForeignKey("warehouses.Warehouse", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    bank_name = models.CharField(max_length=128)
    account_number = models.CharField(max_length=128)
    account_holder = models.CharField(max_length=128)
    ifsc_code = models.CharField(max_length=128)
    branch = models.CharField(max_length=128)
    account_type = models.CharField(max_length=128,choices=BANK_ACCOUNT_TYPE)

    opening_balance_type = models.CharField(max_length=128, choices=OPENING_TYPE, default="debit")
    opening_balance = models.DecimalField(default=0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        db_table = 'finance_bank_account'
        verbose_name = _('Bank Account')
        verbose_name_plural = _('Bank Accounts')
        ordering = ('bank_name',)

    def __unicode__(self):
        return self.bank_name

    def __str__(self):
        return str(self.bank_name)


class SubledgerOpening(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, related_name="value_%(class)s_objects", on_delete=models.CASCADE, blank=True, null=True)
    account_head = models.ForeignKey('finance.AccountHead', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    # warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    sub_ledger = models.CharField(max_length=30, blank=True, null=True)
    sub_ledger_type = models.IntegerField(choices=SUBLEDGEROPENING_SUB_LEDGER_TYPES, blank=True, null=True)
    amount_type = models.IntegerField(choices=SUBLEDGEROPENING_AMOUNT_TYPES, blank=True, null=True)
    amount = models.DecimalField(default=0.00, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.0000'))])

    class Meta:
        db_table = 'finance_subledger_opening'
        verbose_name = _('Subledger Opening')
        verbose_name_plural = _('Subledger Openings')
        ordering = ('-financial_year',)

    def __str__(self):
        return str(self.amount)


class AccountHeadOpening(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, related_name="value_%(class)s_objects", on_delete=models.CASCADE, blank=True, null=True)
    account_head = models.ForeignKey('finance.AccountHead', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    amount_type = models.CharField(max_length=16, choices=ACCOUNTHEADPENING_AMOUNT_TYPES, blank=True, null=True)
    amount = models.DecimalField(default=0.00, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.0000'))])

    class Meta:
        db_table = 'finance_account_head_opening'
        verbose_name = _('Account Head Opening')
        verbose_name_plural = _('Account Head Openings')
        ordering = ('-financial_year',)

    def __str__(self):
        return str(self.amount)


class PaymentVoucher(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    account_head = models.ForeignKey('finance.AccountHead', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    bank = models.ForeignKey('finance.BankAccount', limit_choices_to={'is_deleted': False}, blank=True, null=True, on_delete=models.CASCADE)

    voucher_number = models.CharField(max_length=128)
    voucher_date = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=128, blank=True, null=True)
    sub_ledger = models.CharField(max_length=128, null=True, blank=True)  # to save pk of sub-ledger
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount_type = models.IntegerField(choices=PAYMENTVOUCHER_AMOUNT_TYPES, default=20)

    transfer_type = models.IntegerField(choices=PAYMENTVOUCHER_TRANSFER_TYPES)  # Type of account( from cash/bank )
    is_system_generated = models.BooleanField(default=False)
    cheque_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)  # date entered on cheque
    cheque_status = models.IntegerField(choices=PAYMENTVOUCHER_CHEQUE_STATUS, blank=True, null=True)
    cheque_status_date = models.DateField(blank=True, null=True)  # date of updation of cheque status

    draft_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    draft_date = models.DateField(blank=True, null=True)
    transfer_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    transfer_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'finance_payment_voucher'
        verbose_name = _('Payment Voucher')
        verbose_name_plural = _('Payment Vouchers')
        ordering = ('title',)

    def __str__(self):

        return self.account_head.name


class ReceiptVoucher(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    account_head = models.ForeignKey('finance.AccountHead', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    bank = models.ForeignKey('finance.BankAccount', limit_choices_to={'is_deleted': False}, blank=True, null=True, on_delete=models.CASCADE)
    voucher_date = models.DateTimeField(blank=True, null=True)  # date entered on cheque

    voucher_number = models.CharField(max_length=128)
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=128, blank=True, null=True)
    sub_ledger = models.CharField(max_length=128, null=True, blank=True)  # to save pk of sub-ledger
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount_type = models.IntegerField(choices=RECEIPTVOUCHER_AMOUNT_TYPES, default=10)
    transfer_type = models.IntegerField(choices=RECEIPTVOUCHER_TRANSFER_TYPES)  # Type of account( from cash/bank )
    is_system_generated = models.BooleanField(default=False)
    cheque_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)  # date entered on cheque
    cheque_status = models.IntegerField(choices=RECEIPTVOUCHER_CHEQUE_STATUS, blank=True, null=True)
    cheque_status_date = models.DateField(blank=True, null=True)  # date of updation of cheque status

    draft_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    draft_date = models.DateField(blank=True, null=True)
    transfer_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    transfer_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'finance_receipt_voucher'
        verbose_name = _('Receipt Voucher')
        verbose_name_plural = _('Receipt Vouchers')
        ordering = ('title',)

    def __str__(self):

        return self.account_head.name


class JournalVoucher(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    voucher_number = models.PositiveIntegerField(unique=True)
    voucher_date = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=128, blank=True, null=True)
    sub_ledger = models.CharField(max_length=128, null=True, blank=True)  # to save pk of sub-ledger
    debit_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    credit_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        db_table = 'finance_journal_voucher'
        verbose_name = _('Journal Voucher')
        verbose_name_plural = _('Journal Vouchers')
        ordering = ('title',)

    def credit_total(self):
        credit_total = JournalVoucherItem.objects.filter(journal=self, amount_type=JOURNALVOUCHERITEM_AMOUNT_TYPES.credit).aggregate(credit_total=models.Sum('amount'),).get('credit_total', 0)
        return credit_total or 0

    def debit_total(self):
        debit_total = JournalVoucherItem.objects.filter(journal=self, amount_type=JOURNALVOUCHERITEM_AMOUNT_TYPES.debit).aggregate(debit_total=models.Sum('amount'),).get('debit_total', 0)
        return debit_total or 0

    def __str__(self):
        return self.title


class JournalVoucherItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_deleted = models.BooleanField(default=False)

    journal = models.ForeignKey('finance.JournalVoucher', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    account_head = models.ForeignKey('finance.AccountHead', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    sub_ledger = models.CharField(max_length=128, null=True, blank=True)  # to save pk of sub-ledger
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount_type = models.IntegerField(choices=JOURNALVOUCHERITEM_AMOUNT_TYPES)
    deleted_reason = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        db_table = 'finance_journal_voucher_item'
        verbose_name = _('Journal Voucher Item')
        verbose_name_plural = _('Journal Voucher Items')
        ordering = ('amount_type',)

    def __str__(self):
        return str(self.amount_type)


class CreditNoteVoucher(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, related_name="value_%(class)s_objects", on_delete=models.CASCADE, blank=True, null=True)
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    sale_return = models.ForeignKey("sales.SaleReturn", limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)
    customer = models.ForeignKey('customers.Customer', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    bank = models.ForeignKey('finance.BankAccount', limit_choices_to={'is_deleted': False}, blank=True, null=True, on_delete=models.CASCADE)
    # voucher_code
    voucher_date = models.DateTimeField(blank=True, null=True)  # date entered on cheque
    voucher_number = models.PositiveIntegerField()
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=128, blank=True, null=True)
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount_type = models.IntegerField(choices=CREDITNOTE_AMOUNT_TYPES, default=20)
    transfer_type = models.IntegerField(choices=CREDITNOTE_TRANSFER_TYPES)  # Type of account( from cash/bank )
    is_system_generated = models.BooleanField(default=False)
    cheque_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)  # date entered on cheque
    cheque_status = models.IntegerField(choices=CREDITNOTE_CHEQUE_STATUS, blank=True, null=True)
    cheque_status_date = models.DateField(blank=True, null=True)  # date of updation of cheque status

    draft_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    draft_date = models.DateField(blank=True, null=True)

    transfer_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    transfer_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'finance_credit_voucher'
        verbose_name = _('Credit note Voucher')
        verbose_name_plural = _('Credit note Vouchers')
        ordering = ('-transfer_date',)

    def __str__(self):

        return self.title


class DebitNoteVoucher(BaseModel):
    financial_year = models.ForeignKey('finance.FinancialYear', limit_choices_to={'is_deleted': False}, related_name="value_%(class)s_objects", on_delete=models.CASCADE, blank=True, null=True)
    warehouse = models.ForeignKey("warehouses.Warehouse",  limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE)

    purchase_return = models.ForeignKey('purchases.PurchaseReturn', on_delete=models.CASCADE, limit_choices_to={"is_deleted": False})
    supplier = models.ForeignKey('suppliers.Supplier', limit_choices_to={'is_deleted': False}, on_delete=models.CASCADE, blank=True, null=True)
    bank = models.ForeignKey('finance.BankAccount', limit_choices_to={'is_deleted': False}, blank=True, null=True, on_delete=models.CASCADE)
    # voucher_code
    voucher_date = models.DateTimeField(blank=True, null=True)  # date entered on cheque
    voucher_number = models.PositiveIntegerField()
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=128, blank=True, null=True)
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=15, validators=[MinValueValidator(Decimal('0.00'))])
    amount_type = models.IntegerField(choices=DEBITNOTE_AMOUNT_TYPES, default=20)
    transfer_type = models.IntegerField(choices=DEBITNOTE_TRANSFER_TYPES)  # Type of account( from cash/bank )
    is_system_generated = models.BooleanField(default=False)
    cheque_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    cheque_date = models.DateField(blank=True, null=True)  # date entered on cheque
    cheque_status = models.IntegerField(choices=DEBITNOTE_CHEQUE_STATUS, blank=True, null=True)
    cheque_status_date = models.DateField(blank=True, null=True)  # date of updation of cheque status

    draft_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    draft_date = models.DateField(blank=True, null=True)

    transfer_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    transfer_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'finance_debit_voucher'
        verbose_name = _('Debit note Voucher')
        verbose_name_plural = _('Debit note Vouchers')
        ordering = ('-transfer_date',)

    def __str__(self):

        return self.title
