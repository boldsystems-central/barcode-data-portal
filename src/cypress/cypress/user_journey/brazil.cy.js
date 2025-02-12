describe('User Journey Test - Brazil', () => {
    let recordId = "ABLCW913-10";
    let binId = "BOLD:ACF4938"
    let downloadFileName = "BOLD_ACF4938.tsv"
    it('Researcher from Brazil needs example data to process, is interested in a record that has been BIN\'d, wants records associated with BIN', () => {
        cy.on('uncaught:exception', (err, runnable) => {
            return false;
        });

        cy.visit('/');

        cy.contains('a.nav-link.page-scroll', 'Countries and Oceans').click();

        cy.url().should('include', 'geo');

        cy.get('path[data-code="BR"]').click();

        cy.url().should('include', 'geo/Brazil');

        cy.get('div.col').contains('Specimens:')
        .parents('.col')
        .find('span')
        .eq(1) // Select the second span
        .invoke('text')
        .then((text) => {
            const specimenNumber = parseInt(text, 10);
            expect(specimenNumber).to.be.a('number');
            expect(specimenNumber).to.be.greaterThan(0);
        });

        cy.get('#resultsTable')
        .first()
        .find('td')
        .first()
        .invoke('text')
        .then((text) => {
            expect(text.trim()).to.equal(recordId);
        });

        cy.get('#resultsTable')
        .first()
        .find('td')
        .first()
        .find('a')
        .click();

        cy.url().should('include', `record/${recordId}`);

        cy.get('td.wordwrap.preformatted')
        .invoke('text')
        .then((text) => {
            expect(text.length).to.be.at.least(486);
        });

        cy.get('tr')
        .contains('th', 'BIN ID:')
        .siblings('td')
        .find('a')
        .click();

        cy.url().should('include', `bin/${binId}`);

        cy.get('a[download="BOLD:ACF4938.tsv"]')
        .click();

        const downloadsFolder = Cypress.config('downloadsFolder');
        const filePath = `${downloadsFolder}/${downloadFileName}`;

        cy.readFile(filePath, { timeout: 15000 })
        .should('exist')
        .then((fileContent) => {
            cy.task('getFileSize', filePath).then((fileSize) => {
                expect(fileSize).to.be.gt(0);
            });

            expect(fileContent).to.contain(recordId);
        });
    });
});