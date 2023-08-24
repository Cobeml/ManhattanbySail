// receives a post with deal info, amount, customer name, and customer email and reponds with two payment buttons to be included in quote
const hubspot = require('@hubspot/api-client');
const config = require('./config');
const stripe = require('stripe')(config.apiKey);



async function sendInvoiceACH(customerName, email, dealName, dealId, installmentAmount, dueDate) {
    const customer = await stripe.customers.create({
        name: customerName,
        email: email,
    });

    console.log(customer);

    const invoice = await stripe.invoices.create({
        customer: customer.id,
        collection_method: 'send_invoice',
        days_until_due: 90,
        description: dealName + ' (' + dealId + ')' + '\n' + 'Due: ' + dueDate,
        payment_settings: {
        payment_method_types:[`us_bank_account`]
        },
    });

    console.log(invoice);

    const invoiceItem = await stripe.invoiceItems.create({
        customer: customer.id,
        amount: installmentAmount,
        invoice: invoice.id,
        description: 'Deposit',
    });

    console.log(invoiceItem);

    const finalInvoice = await stripe.invoices.finalizeInvoice(invoice.id);

    console.log(finalInvoice);

    const intent = finalInvoice.payment_intent;

    const paymentIntent = await stripe.paymentIntents.update(
        intent,
        {description: dealId}
    );

    return finalInvoice.hosted_invoice_url;
}

async function sendInvoiceCard(customerName, email, dealName, dealId, installmentAmount, dueDate) {
    const customer = await stripe.customers.create({
        name: customerName,
        email: email,
    });
    
    console.log(customer);

    const invoice = await stripe.invoices.create({
        customer: customer.id,
        collection_method: 'send_invoice',
        days_until_due: 90,
        description: dealName + ' (' + dealId + ')' + '\n' + 'Due: ' + dueDate,
        payment_settings: {
        payment_method_types:[`card`]
        },
    });

    console.log(invoice);

    const invoiceItem = await stripe.invoiceItems.create({
        customer: customer.id,
        amount: installmentAmount,
        invoice: invoice.id,
        description: 'Deposit via Card',
    });

    console.log(invoiceItem);

    let convenienceFee;

    convenienceFee = await stripe.invoiceItems.create({
        customer: customer.id,
        amount: Math.ceil(installmentAmount * .03),
        invoice: invoice.id,
        description: '3% Convenience Fee',
    });

    console.log(convenienceFee);

    const finalInvoice = await stripe.invoices.finalizeInvoice(invoice.id);

    console.log(finalInvoice);

    const intent = finalInvoice.payment_intent;

    const paymentIntent = await stripe.paymentIntents.update(
        intent,
        {description: dealId}
    );

    return finalInvoice.hosted_invoice_url;
}

exports.handler = async(event) => {
    let body = JSON.parse(event.body);
    
    console.log(body);
    const customerName = body.customerName;
    const email = body.email;
    const dealName = body.dealName;
    const dealId = body.dealId;
    const installmentAmount = body.installmentAmount;

    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); 
    var yyyy = today.getFullYear();

    today = mm + '/' + dd + '/' + yyyy;

    let ACHLink;
    let cardLink;
    try {
        ACHLink = await sendInvoiceACH(customerName, email, dealName, dealId, installmentAmount, today);
        cardLink = await sendInvoiceCard(customerName, email, dealName, dealId, installmentAmount, today);
    } catch {
        ACHLink = "error";
        cardLink = "error";
    }

    const hubspotClient = new hubspot.Client({"accessToken": body.accessToken});
    
    const properties = {
        "ach_link": ACHLink,
        "card_link": cardLink,
        "ach_button": "<button class=\"payment-button\" onclick=\"window.open(\'" + ACHLink + "\', \'_blank\')\">{{ \"Pay via ACH (No Fee)\" }}</button>",
        "card_button": "<button class=\"payment-button\" onclick=\"window.open(\'" + cardLink + "\', \'_blank\')\">{{ \"Pay via Card (3% Fee)\" }}</button>"
    };
    const SimplePublicObjectInput = { properties };
    const idProperty = undefined;
    
    try {
        const apiResponse = await hubspotClient.crm.deals.basicApi.update(dealId, SimplePublicObjectInput, idProperty);
        console.log(JSON.stringify(apiResponse, null, 2));
    } catch (e) {
        e.message === 'HTTP request failed'
            ? console.error(JSON.stringify(e.response, null, 2))
            : console.error(e)
        return {
            statusCode: 300,
            body: JSON.stringify("Error"),
        };
    }

    const links = {
        ACHLink: ACHLink,
        cardLink: cardLink
    }    
    return {
        statusCode: 200,
        body: JSON.stringify(links),
    };
};
