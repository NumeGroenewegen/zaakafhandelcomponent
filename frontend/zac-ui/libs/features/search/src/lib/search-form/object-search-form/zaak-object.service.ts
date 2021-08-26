import {Injectable} from '@angular/core';
import {ApplicationHttpClient} from '@gu/services';
import {Observable} from 'rxjs';
import {Geometry, ZaakObject} from "@gu/models";

@Injectable({
  providedIn: 'root'
})
export class ZaakObjectService {
  constructor(private http: ApplicationHttpClient) {
  }

  /**
   * Search for objects in the Objects API
   * @param {Geometry} geometry
   * @param {string} [query]
   * @return {Observable}
   */
  searchObjects(geometry: Geometry, query: string = ''): Observable<ZaakObject[]> {
    const endpoint = encodeURI("/api/core/objects");
    const search = {
      geometry: {
        within: geometry
      },
    }

    if (query) {
      search['data_attrs'] = this._parseQuery(query);
    }

    return this.http.Post<ZaakObject[]>(endpoint, search);
  }

  /**
   * Converts a human-readable query to a valid API data_attrs value.
   * @param {string} query e.q.: "Naam van object" or "adres:Utrechtsestraat, type:Laadpaal"
   * @return {string} Value suitable for data_attrs argument.
   * @private
   */
  _parseQuery(query: string): string {
    return query.split(',')
      .map((part) => part.match(':') ? part : `name:${part}`)
      .map((keyValue) => keyValue.replace(/:\s*/g, ':').trim())
      .map((keyValue) => keyValue.replace(':', '__exact__'))
      .join(',');
  }
}