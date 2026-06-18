from django.urls import re_path, path
from django.conf.urls import include
from . import views

app_name = "finance"

urlpatterns = [
    re_path(r'^account-group-autocomplete/$', views.AccountGroupAutocomplete.as_view(), name='account_group_autocomplete'),
    re_path(r'^account-head-autocomplete/$', views.AccountHeadAutocomplete.as_view(), name='account_head_autocomplete'),
    re_path(r'^bank-autocomplete/$', views.BankaccountAutocomplete.as_view(), name='bankaccount_autocomplete',),

    re_path(r'^create/financial-year/$', views.create_financial_year,name='create_financial_year'),
    re_path(r'^edit/financial-year/(?P<pk>.*)/$',views.edit_financial_year, name='edit_financial_year'),
    re_path(r'^financial-year/view/(?P<pk>.*)/$',views.financial_year, name='financial_year'),
    re_path(r'^delete-financial-year/(?P<pk>.*)/$',views.delete_financial_year, name='delete_financial_year'),
    re_path(r'^financial-years/$', views.financial_years,name='financial_years'),

    re_path(r'^account-groups/create/$', views.create_account_group, name='create_account_group'),
    re_path(r'^account-group/view/(?P<pk>.*)/$', views.account_group, name='account_group'),
    re_path(r'^account-groups/$', views.account_groups, name='account_groups'),
    re_path(r'^edit/account-group/(?P<pk>.*)/$', views.edit_account_group, name='edit_account_group'),
    re_path(r'^delete-account-group/(?P<pk>.*)/$', views.delete_account_group, name='delete_account_group'),

    re_path(r'^bank-account/create/$', views.create_bank_account, name='create_bank_account'),
    re_path(r'^bank-account/edit(?P<pk>.*)/$', views.edit_bank_account, name='edit_bank_account'),
    re_path(r'^bank-accounts/$', views.bank_accounts, name='bank_accounts'),
    re_path(r'^bank-account/view/(?P<pk>.*)/$', views.bank_account, name='bank_account'),
    re_path(r'^bank-account/delete/(?P<pk>.*)/$', views.delete_bank_account, name='delete_bank_account'),

    re_path(r'^account-heads/create/$', views.create_account_head, name='create_account_head'),
    re_path(r'^account-head/view/(?P<pk>.*)/$', views.account_head, name='account_head'),
    re_path(r'^account-heads/$', views.account_heads, name='account_heads'),
    re_path(r'^edit/account-head/(?P<pk>.*)/$', views.edit_account_head, name='edit_account_head'),
    re_path(r'^delete-account-head/(?P<pk>.*)/$', views.delete_account_head, name='delete_account_head'),

    re_path(r'^create/payment-voucher/$', views.create_payment_voucher, name='create_payment_voucher'),
    re_path(r'^edit/payment-voucher/(?P<pk>.*)/$', views.edit_payment_voucher, name='edit_payment_voucher'),
    re_path(r'^payment-voucher/view/(?P<pk>.*)/$', views.payment_voucher, name='payment_voucher'),
    re_path(r'^payment-voucher/print/(?P<pk>.*)/$', views.print_payment_voucher, name='print_payment_voucher'),
    re_path(r'^cancel-payment-voucher/(?P<pk>.*)/$', views.delete_payment_voucher, name='delete_payment_voucher'),
    re_path(r'^payment-vouchers/$', views.payment_vouchers, name='payment_vouchers'),
    re_path(r'^cancelled-payment-vouchers/$', views.cancelled_payment_vouchers, name='cancelled_payment_vouchers'),

    re_path(r'^create/receipt-voucher/$', views.create_receipt_voucher, name='create_receipt_voucher'),
    re_path(r'^edit/receipt-voucher/(?P<pk>.*)/$', views.edit_receipt_voucher, name='edit_receipt_voucher'),
    re_path(r'^receipt-voucher/view/(?P<pk>.*)/$', views.receipt_voucher, name='receipt_voucher'),
    re_path(r'^cancel-receipt-voucher/(?P<pk>.*)/$', views.delete_receipt_voucher, name='delete_receipt_voucher'),
    re_path(r'^receipt-voucher/print/(?P<pk>.*)/$', views.print_receipt_voucher, name='print_receipt_voucher'),
    re_path(r'^receipt-vouchers/$', views.receipt_vouchers, name='receipt_vouchers'),
    re_path(r'^cancelled-receipt-vouchers/$', views.cancelled_receipt_vouchers, name='cancelled_receipt_vouchers'),

    re_path(r'^create/journal-voucher/$', views.create_journal_voucher, name='create_journal_voucher'),
    re_path(r'^edit/journal-voucher/(?P<pk>.*)/$', views.edit_journal_voucher, name='edit_journal_voucher'),
    re_path(r'^journal-voucher/view/(?P<pk>.*)/$', views.journal_voucher, name='journal_voucher'),
    re_path(r'^journal-vouchers/$', views.journal_vouchers, name='journal_vouchers'),
    re_path(r'^delete/journal-voucher/(?P<pk>.*)/$', views.delete_journal_voucher, name='delete_journal_voucher'),

    re_path(r'^create/credit-note-voucher/$', views.create_credit_note_voucher, name='create_credit_note_voucher'),
    re_path(r'^edit/credit-note-voucher/(?P<pk>.*)/$', views.edit_credit_note_voucher, name='edit_credit_note_voucher'),
    re_path(r'^credit-note-voucher/view/(?P<pk>.*)/$', views.credit_note_voucher, name='credit_note_voucher'),
    re_path(r'^cancel-credit-note-voucher/(?P<pk>.*)/$', views.delete_credit_note_voucher, name='delete_credit_note_voucher'),
    re_path(r'^credit-note-vouchers/$', views.credit_note_vouchers, name='credit_note_vouchers'),
    # re_path(r'^cancelled-credit-note-vouchers/$', views.cancelled_credit_note_vouchers, name='cancelled_credit_note_vouchers'),

    re_path(r'^create/debit-note-voucher/$', views.create_debit_note_voucher, name='create_debit_note_voucher'),
    re_path(r'^edit/debit-note-voucher/(?P<pk>.*)/$', views.edit_debit_note_voucher, name='edit_debit_note_voucher'),
    re_path(r'^debit-note-voucher/view/(?P<pk>.*)/$', views.debit_note_voucher, name='debit_note_voucher'),
    re_path(r'^cancel-debit-note-voucher/(?P<pk>.*)/$', views.delete_debit_note_voucher, name='delete_debit_note_voucher'),
    re_path(r'^debit-note-vouchers/$', views.debit_note_vouchers, name='debit_note_vouchers'),
    # re_path(r'^cancelled-debit-note-vouchers/$', views.cancelled_debit_note_vouchers, name='cancelled_debit_note_vouchers'),

    path('create-invoice-prifix/', views.create_invoice_prifix, name='create_invoice_prifix'),
    path('invoice-prifixs/', views.invoice_prifixs, name='invoice_prifixs'),
    re_path(r'^edit-invoice-prifix/(?P<pk>.*)/$', views.edit_invoice_prifix, name='edit_invoice_prifix'),
    re_path(r'^view-invoice-prifix/(?P<pk>.*)/$', views.invoice_prifix, name='invoice_prifix'),
    re_path(r'^delete-invoice-prifix/(?P<pk>.*)/$',views.delete_invoice_prifix, name='delete_invoice_prifix'),
    path('delete-selected-invoice-prifixs/', views.delete_selected_invoice_prifixs,name='delete_selected_brands'),
    path('get-account-head/', views.get_account_head,name='get_account_head'),

]
