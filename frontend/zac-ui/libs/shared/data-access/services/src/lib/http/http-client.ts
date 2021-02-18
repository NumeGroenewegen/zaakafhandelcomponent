import {HttpClient, HttpHeaders, HttpParams} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';

export interface IRequestOptions {
  headers?: HttpHeaders;
  observe?: any;
  params?: HttpParams;
  reportProgress?: boolean;
  responseType?: any;
  withCredentials?: boolean;
  body?: any;
}

export function applicationHttpClientCreator(http: HttpClient) {
  return new ApplicationHttpClient(http);
}

@Injectable({
  providedIn: 'root'
})
export class ApplicationHttpClient {

  public constructor(public http: HttpClient) {}

  public Get<T>(endPoint: string, options?: IRequestOptions): Observable<T> {
    return this.http.get<T>(endPoint, options);
  }

  public Post<T>(endPoint: string, params?: any, options?: IRequestOptions): Observable<T> {
    const defaultOptions = { withCredentials: true }
    const mergedOptions = {...defaultOptions, ...options};
    return this.http.post<T>(endPoint, params, mergedOptions);
  }

  public Put<T>(endPoint: string, params?: any, options?: IRequestOptions): Observable<T> {
    options = { withCredentials: true }
    return this.http.put<T>(endPoint, params, options);
  }

  public Delete<T>(endPoint: string, options?: IRequestOptions): Observable<T> {
    options = { withCredentials: true }
    return this.http.delete<T>(endPoint, options);
  }
}
