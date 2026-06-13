# Theme Coverage Audit

This audit checks whether the stock pool is broad enough for cross-sectional research and theme-level validation. It is not evidence of forecast accuracy.

## Summary

- Requested themes: `professional`
- Unique symbols: `145`
- Minimum symbols before any trusted prediction can be considered: `200`
- Theme rows audited: `14`
- Themes that can support trusted evidence after model/data gates: `0`
- Coverage status counts: `{'ready': 14}`

## Thin Or Blocked Themes

- `rare_earth_magnetic_materials` (professional_hot): 8/8 symbols, status=`ready`, sample=`600111;000831;600392;000970;002056;300224;002600;300748`
- `advanced_packaging_chiplet_pcb` (professional_hot): 9/8 symbols, status=`ready`, sample=`600584;002156;002463;002916;002938;300476;603228;688183`
- `medical_device_ivd_imaging` (professional_hot): 9/8 symbols, status=`ready`, sample=`300760;688271;688617;688029;300482;688575;300003;300595`
- `commercial_space_satellite_internet` (professional_hot): 10/8 symbols, status=`ready`, sample=`600118;688066;688568;002151;300627;002465;300045;688239`
- `cpo_optical_module_datacenter` (professional_hot): 10/8 symbols, status=`ready`, sample=`300308;300502;300394;300570;002281;688498;600522;600487`
- `humanoid_robot_core_parts` (professional_hot): 10/8 symbols, status=`ready`, sample=`688017;002747;300124;002472;603662;300660;301368;002050`
- `industrial_mother_machine_laser` (professional_hot): 10/8 symbols, status=`ready`, sample=`300161;688698;000988;002008;300607;603283;688305;601100`
- `shipbuilding_ocean_shipping` (professional_hot): 10/8 symbols, status=`ready`, sample=`600150;601989;600482;601919;601872;600026;600428;600018`
- `uhv_smart_grid_power_equipment` (professional_hot): 10/8 symbols, status=`ready`, sample=`600406;601179;600312;002028;600089;601877;300001;300491`
- `cxo_biotech_innovative_drug` (professional_hot): 11/8 symbols, status=`ready`, sample=`603259;300759;300347;002821;300363;300725;600276;688235`
- `data_element_fintech_ai_app` (professional_hot): 11/8 symbols, status=`ready`, sample=`300033;300059;300418;300364;002230;688111;600845;300212`
- `solid_state_battery_materials` (professional_hot): 11/8 symbols, status=`ready`, sample=`300750;688567;300073;002709;603659;688116;688388;300390`
- `central_soe_high_dividend` (professional_hot): 12/8 symbols, status=`ready`, sample=`600900;601088;600028;601857;600938;600941;601728;601816`
- `semiconductor_equipment_materials` (professional_hot): 14/8 symbols, status=`ready`, sample=`002371;688012;688072;688120;688037;688019;688200;300604`

## Guardrail

- A broad theme universe only removes the small-pool bottleneck. It must still pass PIT data audit, factor trust audit, walk-forward, calibration, event evidence, and risk gates before any stock forecast can be marked `trusted`.
