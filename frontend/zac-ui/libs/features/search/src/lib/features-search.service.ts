import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApplicationHttpClient } from '@gu/services';
import { ZaaktypeEigenschap } from '../models/zaaktype-eigenschappen';
import { Zaaktype } from '../models/zaaktype';
import { Search } from '../models/search';
import { Zaak } from '@gu/models';

@Injectable({
  providedIn: 'root'
})
export class FeaturesSearchService {

  constructor(private http: ApplicationHttpClient) { }

  getZaaktypen(): Observable<Zaaktype> {
    const endpoint = encodeURI("/api/core/zaaktypen");
    return this.http.Get<Zaaktype>(endpoint);
  }

  getZaaktypeEigenschappen(catalogus, zaaktype_omschrijving): Observable<ZaaktypeEigenschap[]> {
    const endpoint = encodeURI(`/api/core/eigenschappen?catalogus=${catalogus}&zaaktype_omschrijving=${zaaktype_omschrijving}`);
    return this.http.Get<ZaaktypeEigenschap[]>(endpoint);
  }

  postSearchZaken(formData: Search): Observable<Zaak[]> {
    const endpoint = encodeURI("/api/search/zaken");
    return this.http.Post<Zaak[]>(endpoint, formData);
  }
}