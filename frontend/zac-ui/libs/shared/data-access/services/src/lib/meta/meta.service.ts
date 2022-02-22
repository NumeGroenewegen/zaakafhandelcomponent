import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {ApplicationHttpClient} from '@gu/services';
import {CachedObservableMethod} from '@gu/utils';
import { MetaConfidentiality, ZaaktypeEigenschap } from '@gu/models';

@Injectable({
  providedIn: 'root',
})
export class MetaService {
  constructor(private http: ApplicationHttpClient) {
  }

  /**
   * List the available confidentiality classification.
   * @return {Observable}
   */
  @CachedObservableMethod('MetaService.listConfidentialityClassifications')
  listConfidentialityClassifications(): Observable<MetaConfidentiality[]> {
    const endpoint = encodeURI('/api/core/vertrouwelijkheidsaanduidingen');
    return this.http.Get<MetaConfidentiality[]>(endpoint);
  }

  /**
   * Retrieve case type properties by providing catalog and description
   * @param catalogus
   * @param omschrijving
   * @returns {Observable<ZaaktypeEigenschap[]>}
   */
  getZaaktypeEigenschappenByCatalogus(catalogus, omschrijving): Observable<ZaaktypeEigenschap[]> {
    const endpoint = encodeURI(`/api/core/eigenschappen?catalogus=${catalogus}&zaaktype_omschrijving=${omschrijving}`);
    return this.http.Get<ZaaktypeEigenschap[]>(endpoint);
  }

  /**
   * Retrieve case type properties by providing url
   * @param zaaktypeUrl
   * @returns {Observable<ZaaktypeEigenschap[]>}
   */
  getZaaktypeEigenschappenByUrl(zaaktypeUrl): Observable<ZaaktypeEigenschap[]> {
    const endpoint = encodeURI(`/api/core/eigenschappen?zaaktype=${zaaktypeUrl}`);
    return this.http.Get<ZaaktypeEigenschap[]>(endpoint);
  }
}
