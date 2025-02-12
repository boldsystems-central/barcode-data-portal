const endpoints = [
    {
        url: '/api/maps/eAFLT823KijKL8vMS07VLy5JLEm18s8rSSzKzLfOyczNLElNAQDp5A1l',
        method: 'GET',
        body: {},
        qs: {
            offset: 0
        },
        headers: {},
        expectedStatus: 200,
        failOnStatusCode: true,
        isDownload: true
    }
];
const path = require('path');

// Test Endpoint
describe('Test maps endpoint', () => {
    endpoints.forEach((endpoint, index) => {
        it(`should return ${endpoint.expectedStatus} for ${endpoint.url}`, () => {
            cy.request({
                method: endpoint.method,
                url: endpoint.url,
                body: endpoint.body,
                qs: endpoint.qs,
                headers: endpoint.headers,
                failOnStatusCode: endpoint.failOnStatusCode,
                timeout: 500
            }).then((response) => {
                expect(response.status).to.eq(endpoint.expectedStatus);    
                if (endpoint.expectedStatus === 200) {
                    expect(response.body).to.not.be.empty;
                    if (endpoint.expectedkeys != null){
                        endpoint.expectedkeys.forEach(key => {
                            expect(response.body).to.have.property(key);
                            const value = response.body[key];
                            if (typeof value === 'string') {
                                expect(value).to.not.be.empty;
                            } else if (typeof value === 'number') {
                                expect(value).to.not.be.NaN;
                            }
                        });
                    }
                    if (endpoint.expectedKeyValues != null){
                        Object.entries(endpoint.expectedKeyValues).forEach(([key, expected_value]) => {
                            const value = response.body[key];
                            expect(value).to.equal(expected_value);
                        });
                    }
                    if (endpoint.resultArrayMinLen != null){
                        expect(response.body).to.be.an('array');
                        expect(response.body.length).to.be.at.least(endpoint.resultArrayMinLen);
                    }
                }
            });
            if (endpoint.isDownload){
                let baseUrl = Cypress.config('baseUrl');
                let sanitizedBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
                let queryString = new URLSearchParams(endpoint.qs).toString();
                let fileUrl = `${sanitizedBaseUrl}${endpoint.url}?${queryString}`;
                const downloadsFolder = Cypress.config('downloadsFolder');
                cy.downloadFile(fileUrl, downloadsFolder, `${endpoint.url}`);
                const filePath = path.join(downloadsFolder, `${endpoint.url}`);
                cy.readFile(filePath, 'utf8').then((fileContent) => {
                    expect(fileContent.length).to.be.greaterThan(0);
                });
            }
        });
    });
});

// Benchmark Endpoint
import benchmark from 'cypress-benchmark';

const benchmarkFolder = Cypress.config('benchmarkFolder');
const options = {
    outPath : `${benchmarkFolder}/benchmark_api.json`,
    merge : true,
    runCount: 1
}
endpoints.forEach((endpoint, index) => {
    benchmark(`Benchmark Test for maps`, options, () => {
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
