describe('User Journey Test - Search', () => {
    it('View the search page and search for specimens in Canada', () => {
        cy.visit('/search');

        cy.get('#query').type('Canada');

        cy.get('.dropdown-item')
        .contains('Canada[geo]')
        .click();

        cy.get('button')
        .contains('Search')
        .click();

        cy.url().should('include', 'query=Canada[geo]');

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
    });
});