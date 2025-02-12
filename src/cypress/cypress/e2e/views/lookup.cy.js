const endpoints = [
    {
        url: '/lookup/test',
        method: 'GET',
        body: {},
        qs: {},
        headers: {},
        expectedStatus: 200,
        failOnStatusCode: true
    }
]

// Test View
describe('Test lookup Webpage', () => {
    endpoints.forEach((endpoint) => {
        it(`Tests for ${endpoint.url}`, () => {
            if(endpoint.expectedStatus == 200){
                cy.intercept({ method: 'GET', url: '/api/**' }, (req) => {
                    let startTime = Date.now();
                    req.continue((res) => {
                        expect(res.statusCode, `Request to ${res.url} failed with status ${res.statusCode}`).to.be.lessThan(400);
                        const endTime = Date.now();
                        const timeSpent = endTime - startTime;
                        expect(timeSpent, `Request to ${res.url} took ${timeSpent}ms`).to.be.lessThan(1000);
                        startTime = Date.now();
                        if (req.url.includes('/api/maps/') || req.url.includes('/api/sequence/') || req.url.includes('/api/qr-code/')) {
                            return;
                        }
                        const responseSize = JSON.stringify(res.body).length;
                        expect(responseSize, `Response to ${res.url} is too small (${responseSize} bytes)`).to.be.greaterThan(10);
                    });
                }).as('allRequests');
                cy.visit({
                    method: endpoint.method,
                    url: endpoint.url,
                    qs: endpoint.qs,
                    headers: endpoint.headers,
                    failOnStatusCode: endpoint.failOnStatusCode
                });
                cy.get('@allRequests.all').then((requests) => {
                    if (requests && requests.length > 0) {
                        cy.wait('@allRequests');
                    } else {
                        // cy.log('No requests to /api/** occurred.');
                    }
                });
            }
            
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
                    // expect(titleExists).to.be.true;

                    let expectedString = endpoint.url.replace(new RegExp('^' + '/lookup/'), '');
                    expect(bodyText).to.equal(expectedString);
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
    benchmark(`Benchmark Test for lookup`, options, () => {
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
