export interface CreateCase {
  zaaktypeIdentificatie: string,
  zaaktypeCatalogus: string,
  zaakDetails: {
    omschrijving: string,
    toelichting?: string
  }
}
