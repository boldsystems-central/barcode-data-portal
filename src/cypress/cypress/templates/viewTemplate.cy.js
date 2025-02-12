// Replace "template" with your view
const endpoints = [
    {
        url: '/about', // Enter the endpoint url here
        method: 'GET', // Use GET method to view page
        body: {}, // Request Body
        qs: { // Query parameters
            query: "geo:province/state:Ontario",
            extent: "limited"
        },
        headers: {}, // Request header
        expectedStatus: 200, // Expected to get 200-OK from webpage
        failOnStatusCode: true, // Fail on test if response code is not 200-OK
        // tableID: "resultsTable",
        // tableMinLen: 10,
    }
]

// Test View
describe('Test template Webpage', () => {
    endpoints.forEach((endpoint) => {
        it(`Tests for ${endpoint.url}`, () => {
            if(endpoint.expectedStatus == 200){
                // Intercept all outgoing network requests
                cy.intercept({ method: 'GET', url: '/api/**' }, (req) => {
                    let startTime = Date.now();
                    req.continue((res) => {
                        // Check that the response status code is less than 400 (indicates success)
                        expect(res.statusCode, `Request to ${res.url} failed with status ${res.statusCode}`).to.be.lessThan(400);
                        // Capture the end time and calculate the time spent on the request
                        const endTime = Date.now();
                        const timeSpent = endTime - startTime;
                        // Ensure the request-response cycle time is less than 1000ms
                        expect(timeSpent, `Request to ${res.url} took ${timeSpent}ms`).to.be.lessThan(1000);
                        // Reset the start time for the next request
                        startTime = Date.now();
                        if (req.url.includes('/api/maps/') || req.url.includes('/api/sequence/') || req.url.includes('/api/qr-code/')) {
                            return;
                        }
                        // Calculate the size of the response by converting it to a string
                        const responseSize = JSON.stringify(res.body).length;
                        // Ensure the response size is greater than 100 bytes
                        expect(responseSize, `Response to ${res.url} is too small (${responseSize} bytes)`).to.be.greaterThan(10);
                    });
                }).as('allRequests');
                // Load and rendering the page
                cy.visit({
                    method: endpoint.method,
                    url: endpoint.url,
                    qs: endpoint.qs,
                    headers: endpoint.headers,
                    failOnStatusCode: endpoint.failOnStatusCode
                });
                // wait for any ongoing requests to complete
                cy.get('@allRequests.all').then((requests) => {
                    if (requests && requests.length > 0) {
                        cy.wait('@allRequests');
                    } else {
                        // cy.log('No requests to /api/** occurred.');
                    }
                });
            }

            // Check webpage without rendering
            cy.request({
                method: endpoint.method,
                url: endpoint.url,
                body: endpoint.body,
                qs: endpoint.qs,
                headers: endpoint.headers,
                failOnStatusCode: endpoint.failOnStatusCode
            }).then((response) => {
                expect(response.status).to.eq(endpoint.expectedStatus);    
                if (endpoint.expectedStatus === 200) {
                    expect(response.body).to.not.be.empty;

                    const parser = new DOMParser();
                    const doc = parser.parseFromString(response.body, 'text/html');

                    const bodyExists = doc.querySelector('body') !== null;
                    expect(bodyExists).to.be.true;
                    
                    const scripts = doc.querySelectorAll('script');
                    scripts.forEach(script => script.remove());

                    const bodyText = doc.querySelector('body').textContent.toLowerCase();
                    const hasError = bodyText.includes("error");
                    expect(hasError).to.be.false;

                    const notFound = bodyText.includes("not found");
                    expect(notFound).to.be.false;
                    
                    const headExists = doc.querySelector('head') !== null;
                    expect(headExists).to.be.true;

                    const titleExists = doc.querySelector('head > title') !== null;
                    expect(titleExists).to.be.true;
                }
            });
            if (endpoint.tableID != null){
                cy.get(`#${endpoint.tableID} tbody tr`).should('have.length.greaterThan', endpoint.tableMinLen);
            }
        });
    });
});

// Benchmark View
import benchmark from 'cypress-benchmark';

const benchmarkFolder = Cypress.config('benchmarkFolder');
const options = {
    outPath : `${benchmarkFolder}/benchmark_view.json`,
    merge : true,
    runCount: 1
}
endpoints.forEach((endpoint, index) => {
    benchmark(`Benchmark Test for template`, options, () => {
        const startMark = `start_${endpoint.url}`;
        const endMark = `end_${endpoint.url}`;
        const measureName = `Data load time - ${endpoint.url}`;

        cy.mark(startMark);
        cy.request({
            method: endpoint.method,
            url: endpoint.url,
            body: endpoint.body,
            qs: endpoint.qs,
            headers: endpoint.headers,
            timeout: 60000,
            failOnStatusCode: endpoint.failOnStatusCode
        }).then(() => {
            cy.mark(endMark);
            cy.measure(measureName, startMark, endMark);
        });
        cy.wait(100)
    });
});
