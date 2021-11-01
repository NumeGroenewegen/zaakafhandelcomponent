import {CommonModule} from '@angular/common';
import {HttpClientModule, HttpClientXsrfModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {FormGroupDirective, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {TabsModule} from 'ngx-bootstrap/tabs';
import {MultiselectModule, SharedUiComponentsModule} from '@gu/components';
import {FeaturesSearchModule} from '@gu/search';
import {ActiviteitenComponent} from './activiteiten/activiteiten.component';
import {AdviserenAccorderenComponent} from './adviseren-accorderen/adviseren-accorderen.component';
import {DetailModalComponent} from './adviseren-accorderen/detail-modal/detail-modal.component';
import {BetrokkenenComponent} from './betrokkenen/betrokkenen.component';
import {DocumentenModule} from './documenten/documenten.module';
import {FeaturesZaakDetailComponent} from './features-zaak-detail.component';
import {GerelateerdeObjectenComponent} from './gerelateerde-objecten/gerelateerde-objecten.component';
import {GerelateerdeZakenModule} from './gerelateerde-zaken/gerelateerde-zaken.module';
import {InformatieComponent} from './informatie/informatie.component';
import {KetenProcessenModule} from './keten-processen/keten-processen.module';
import {StatusComponent} from './status/status.component';
import {ToegangVerlenenComponent} from './toegang-verlenen/toegang-verlenen.component';
import {ZaakMapComponent} from './zaak-map/zaak-map.component';
import {UserPermissionsComponent} from './user-permissions/user-permissions.component';

@NgModule({
  imports: [
    CommonModule,
    DocumentenModule,
    FormsModule,
    GerelateerdeZakenModule,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'X-CSRFToken',
    }),
    KetenProcessenModule,
    MultiselectModule,
    ReactiveFormsModule,
    FeaturesSearchModule,
    SharedUiComponentsModule,
    TabsModule.forRoot(),
  ],
  declarations: [
    FeaturesZaakDetailComponent,
    InformatieComponent,
    BetrokkenenComponent,
    StatusComponent,
    GerelateerdeObjectenComponent,
    AdviserenAccorderenComponent,
    DetailModalComponent,
    ToegangVerlenenComponent,
    ActiviteitenComponent,
    UserPermissionsComponent,
    ZaakMapComponent,
  ],
  exports: [FeaturesZaakDetailComponent],
  providers: [FormGroupDirective]
})
export class FeaturesZaakDetailModule {
}
