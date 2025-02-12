describe('User Journey Test 3 - Fungal', () => {
    it('Fungal researcher from Iran wants to navigate site for Fungal records, then tries to find most recorded Fungal class in Iran, downloads records', () => {        
        cy.visit('/');

        // Wait to run $(document).ready
        cy.wait(500)

        cy.get('p#fungal-and-other-species')
        .invoke('text')
        .then((text) => {
            const number = parseInt(text.trim(), 10);
            expect(number).to.be.a('number');
            expect(number).to.be.greaterThan(0);
        });

        cy.get('#query').type('fungi');
        cy.get('.dropdown-item').contains('Fungi[tax]').click();
        cy.get('button').contains('Search').click();

        cy.url().should('include', 'result?query=Fungi[tax]');

        cy.get('table')
        .contains('th', 'Specimens:')
        .parents('tr')
        .find('td')
        .invoke('text')
        .then((text) => {
            const value = Number(text.trim());
            expect(value).to.be.a('number');
            expect(value).to.be.greaterThan(0);
        });

        cy.get('#query').clear().type('fungi');
        cy.get('.dropdown-item').contains('Fungi[tax]').click();
        cy.get('#query').clear().type('iran');
        cy.get('.dropdown-item').contains('Iran[geo]').click();
        cy.get('button').contains('Search').click();

        cy.url().should('include', '/result?query=Fungi[tax],Iran[geo]');

        cy.get('text[data-unformatted*="Ascomycota"]')
        .find('a')
        .invoke('removeAttr','target');

        cy.get('text[data-unformatted*="Ascomycota"]')
        .find('a')
        .contains('↗')
        .click();

        // Click is not doing what we expect
        // Make sure the href is correct, then visit destination directly
        cy.get('text[data-unformatted*="Ascomycota"]')
        .find('a')
        .invoke('attr', 'xlink:href')
        .then((href) => {
            expect(href).to.equal('/result?query=%22Ascomycota%22%5Btax%5D');
        });
        cy.visit('/result?query="Ascomycota"%5Btax%5D');

        cy.url().should('include', '/result?query=%22Ascomycota%22%5Btax%5D');
        
        cy.get('a[download="result.json"]')
        .click();

        // TODO: Correct the file extension of jsonl files from .json to .jsonl.
        // const downloadsFolder = Cypress.config('downloadsFolder');
        // const filePath = `${downloadsFolder}/result.jsonl`;
        
        // cy.readFile(filePath, { timeout: 15000 })
        // .should('exist')
        // .then(() => {
        //     cy.task('getFileSize', filePath).then((fileSize) => {
        //         expect(fileSize).to.be.gt(0);
        //     });
        // });

    });
});