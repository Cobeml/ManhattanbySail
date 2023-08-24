// include config file with secrets in current directory
const config = require('./config');
const stripe = require('stripe')(config.stripe);
const hubspot = require('@hubspot/api-client');
const hubspotClient = new hubspot.Client({"accessToken": config.hubspot});

async function getPayments() {
  const payments = [];
  
  let lastRead;
  let amountRead;
  let first = true;
  do {
    let paymentIntents
    if (first === true) {
      paymentIntents = await stripe.paymentIntents.list({
        limit: 100,
      });
    } else {
      paymentIntents = await stripe.paymentIntents.list({
        limit: 100,
        starting_after: lastRead,
      });
    }
    first = false;

    amountRead = paymentIntents.data.length;
    lastRead = paymentIntents.data[amountRead - 1]['id'];

    for (let j = 0; j < paymentIntents.data.length; j++) {
      let createdTimestamp = paymentIntents.data[j].created;
      let d = new Date(createdTimestamp * 1000);
      let timeStampCon = d.getDate() + '/' + (d.getMonth()) + '/' + d.getFullYear() + " " + d.getHours() + ':' + d.getMinutes();
      let amount = paymentIntents.data[j].amount;
      let amount_received = paymentIntents.data[j].amount_received;
      if (amount_received > 0) {
        let dealId = paymentIntents.data[j].description;
        let status = paymentIntents.data[j].status;
        let convenience_fee = 0;
        let convenience_fee_received = 0;
        let cardPayment = false;
        for (let k = 0; k < paymentIntents.data[j].payment_method_types.length; k++) {
          if (paymentIntents.data[j].payment_method_types[k] == 'card') {
            cardPayment = true;
          }
        }
        if (cardPayment) {
          if (status == 'succeeded') {
            convenience_fee_received = amount_received * .03;
            amount_received *= (100 / 103);
          }
          convenience_fee = amount * .03;
          amount *= (100 / 103); 
        } 
        let amount_dollar = Math.round(amount) / 100.0;
        let amount_received_dollar = Math.round(amount_received) / 100.0;
        let fee_dollar = Math.round(convenience_fee) / 100.0;
        let fee_received_dollar = Math.round(convenience_fee_received) / 100.0;

        const infoString = 'Amount: ' + amount_dollar + ' | Fee: ' + fee_dollar + ' | Status: ' + status + ' | Created: ' + timeStampCon + '<br>';

        const info = {
          'dealId': dealId,
          'paymentsString': infoString,
          'amountPaid': amount_received_dollar,
          'feePaid': fee_received_dollar
        }
        payments.push(info);
      }
    }
  } while (amountRead === 100);

  let paymentObj = {}
  for (let i = 0; i < payments.length; i++) {
    paymentObj[payments[i].dealId] = {
      'paymentsString': '',
      'amountPaid': 0,
      'feePaid': 0
    }
  }

  for (let i = 0; i < payments.length; i++) {
    paymentObj[payments[i].dealId].paymentsString += payments[i].paymentsString;
    paymentObj[payments[i].dealId].amountPaid += payments[i].amountPaid;
    paymentObj[payments[i].dealId].feePaid += payments[i].feePaid;
  }

  return paymentObj;
}

async function uploadToHubspot(payments) {
  const dealIds = Object.keys(payments);
  let responses = {};
  for (var i = 0; i < dealIds.length; i++) {
    const dealId = dealIds[i];
    const properties = {
      "payments_via_stripe": payments[dealId].paymentsString,
      "total_paid_via_stripe": payments[dealId].amountPaid,
      "convenience_fees_paid_via_stripe": payments[dealId].feePaid
    };
    const SimplePublicObjectInput = { properties };
    const idProperty = undefined;
    
    try {
      const apiResponse = await hubspotClient.crm.deals.basicApi.update(dealId, SimplePublicObjectInput, idProperty);
      console.log(JSON.stringify(apiResponse, null, 2));
      responses[i] = apiResponse;
    } catch (e) {
      e.message === 'HTTP request failed'
        ? console.error(JSON.stringify(e.response, null, 2))
        : console.error(e)
    }
  }
  return responses;
}

async function regularCheck() {
  const payments = await getPayments();
  const uploads = await uploadToHubspot(payments);
  return uploads;
}
    
regularCheck();
exports.handler = async(event) => {
    const uploads = await regularCheck();
    const response = {
        statusCode: 200,
        body: JSON.stringify(uploads, null, 2),
    };
    return response;
};
