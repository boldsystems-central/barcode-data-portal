const endpoints = [
    {
        url: '/bin',
        method: 'GET',
        body: {},
        qs: {},
        headers: {},
        expectedStatus: 200,
        failOnStatusCode: true,
        tableID: "ancillaryTable",
        tableMinLen: 10
    },
    {
        // url: '/bin/BOLD:AAD7527',
        url: '/bin/BOLD:AAA2953',
        method: 'GET',
        body: {},
        qs: {},
        headers: {},
        expectedStatus: 200,
        failOnStatusCode: true,
        tableID: "resultsTable",
        tableMinLen: 2
    }
]

// Important notes:
// You have 2 options
// A. Wait for long time to capture all request by increasing the wait time in the cy.wait(), e.g 30 seconds.
// B. You can wait less, replace i < callCount with i < INF. when there is no new request, the test will fail but the logs are meaningful.
describe('Subcalls Test', () => {
    endpoints.forEach((endpoint) => {
        it('General data queries', function() {
            // Initialize callCount to keep track of the number of intercepted requests
            let callCount = 0;

            // Set up a Cypress intercept to catch all GET requests and increment the callCount for each
            cy.intercept({ method: 'GET', path: '**' }, (req) => {
                callCount++; // Increment callCount for each intercepted request
                req.alias = `call${callCount}`; // Assign a unique alias to each intercepted request
            }).as('call'); // Alias the intercept group for reference

            // Record the start time before visiting the endpoint
            const startTime = new Date().getTime();

            // Visit the endpoint
            cy.visit({
                method: endpoint.method,
                url: endpoint.url,
                qs: endpoint.qs,
                headers: endpoint.headers,
                failOnStatusCode: endpoint.failOnStatusCode
            });

            // Wait for 1 second to ensure all requests are captured
            cy.wait(1000).then(() => {

                // Log the number of captured calls
                let message = `callCount: ${callCount}`;
                cy.task('log', message);

                // Iterate over the number of intercepted calls
                // for (let i = 0; i < callCount; i++) {
                for (let i = 0; i < 1000; i++) {
                    // Wait for each call
                    cy.wait(`@call${i + 1}`, { timeout: 5000 }).then((interception) => {
                        // Capture the end time and cumulative response time
                        const endTime = new Date().getTime();
                        const responseTime = endTime - startTime;

                        // alternative method to get response time from headers, not available for external requests.
                        // const responseTime = interception.response.headers['x-process-time']; // Get response time

                        // Log the URL of the intercepted request and its response time
                        let message = `Sub-call: ${interception.request.url} | Cumulative Response Time: ${responseTime} ms`;
                        console.log(message);
                        cy.task('log', message);

                        // Check if the response status code indicates an error
                        if (interception.response.statusCode >= 400) {
                            let errorMessage = `Error in sub-call: ${interception.request.url}, Status: ${interception.response.statusCode}`;
                            console.error(errorMessage);
                            cy.task('log', errorMessage);
                        }
                        // Assert that the response status code is less than 400 (no errors)
                        expect(interception.response.statusCode).to.be.lessThan(400);
                    });
                }
            });
        });
    });
});
