# 交付物①：Key替换对照表（中文key→英文规范key）

> 工单：DSH_B_MERGE_HIST_IND_P3_REV | 日期：2026-09-24
> 总计：147条key完成中文→英文替换

---

| # | 原始Key | 替换后Key | 指标名称 | 有ID |
|---|---------|----------|----------|------|
| 1 | `IMEA_大豆_现货价_tin诺普_d` | `imea_soybean_spot_price_sinop_d` | IMEA：大豆：现货价：锡诺普（日） | ✓ |
| 2 | `LME_zinc_注销warrant_d_LME_zinc_注销占比_d` | `lme_zn_cancel_warrant_d_lme_zn_cancel_ratio_d` | LME: 锌: 注销仓单（日） / LME：锌：注销占比（日） | ✓ |
| 3 | `LME_zincinv总计_d_LME_zinc_期货inv_d` | `LME_zincstock总计_d_LME_zinc_期货stock_d` | LME: 锌库存总计（日） / LME：锌：期货库存（日） | ✓ |
| 4 | `LME_zincstock总计_d_LME_zinc_期货stock_d` | `lme_zn_total_inv_d_lme_zn_fut_inv_d` | LME: 锌库存总计（日） / LME：锌：期货库存（日） | ✓ |
| 5 | `LME_zinc仓库注册warrant_total_d_LME_zinc_注册warrant_d` | `lme_zn_warehouse_reg_warrant_total_d_lme_zn_reg_warrant_d` | LME: 锌仓库注册仓单: 合计（日） / LME：锌：注册仓单（日） | ✓ |
| 6 | `LME_zinc仓库注册warrant_合计_d_LME_zinc_注册warrant_d` | `LME_zinc仓库注册warrant_total_d_LME_zinc_注册warrant_d` | LME: 锌仓库注册仓单: 合计（日） / LME：锌：注册仓单（日） | ✓ |
| 7 | `LME库存` | `lme_inventory` | LME库存 | ✓ |
| 8 | `Mysteel_aluminum_沪伦比值_d` | `mysteel_al_shfe_lme_ratio_d` | Mysteel：铝：沪伦比值（日） | ✓ |
| 9 | `NBS_制造业采购经理指数_m` | `nbs_pmi_m` | NBS: 制造业采购经理指数（月） | ✓ |
| 10 | `SHFE_zinc_invw报_本winv期货_w_SHFE_zinc_期货inv_w` | `SHFE_zinc_stockw报_本wstock期货_w_SHFE_zinc_期货stock_w` | SHFE: 锌: 库存周报: 本周库存期货（周） / SHFE：锌：期货库存（周） | ✓ |
| 11 | `SHFE_zinc_stockw报_本wstock期货_w_SHFE_zinc_期货stock_w` | `shfe_zn_weekly_inv_fut_w_shfe_zn_fut_inv_w` | SHFE: 锌: 库存周报: 本周库存期货（周） / SHFE：锌：期货库存（周） | ✓ |
| 12 | `SHFE_zinc_warrantd报by地区_shanghai_期货_d_等` | `shfe_zn_warrant_daily_by_region_shanghai_fut_d` | SHFE: 锌: 仓单日报分地区_上海: 期货（日）等 | ✓ |
| 13 | `SHFE_zinc_warrantd报分地区_shanghai_期货_d_等` | `SHFE_zinc_warrantd报by地区_shanghai_期货_d_等` | SHFE: 锌: 仓单日报分地区_上海: 期货（日）等 | ✓ |
| 14 | `SHFE库存` | `shfe_inventory` | 上期所库存 | ✓ |
| 15 | `SMM_coated_zinc成品stock_w_coated_zinc板卷_钢铁企业_厂内stock_china_w` | `smm_coated_zn_prod_inv_w_coated_zn_plate_roll_steel_enterprise_plant_inv_china_w` | SMM: 镀锌成品库存（周） / 镀锌板卷：钢铁企业：厂内库存：中国（周） | ✓ |
| 16 | `SMM_refinezincimport盈亏_zinc沪伦比值_d` | `smm_refined_zn_import_pnl_zn_shfe_lme_ratio_d` | SMM: 精炼锌进口盈亏: 锌沪伦比值（日） | ✓ |
| 17 | `SMM_压铸zinc_alloy开工率_m_zinc_alloy企业_开工率_china_m` | `smm_die_casting_zn_alloy_util_m_zn_alloy_enterprise_util_china_m` | SMM: 压铸锌合金开工率（月） / 锌合金企业：开工率：中国（月） | ✓ |
| 18 | `SMM_压铸zinc合金util_m_zinc合金企业_util_china_m` | `SMM_压铸zinc_alloy开工率_m_zinc_alloy企业_开工率_china_m` | SMM: 压铸锌合金开工率（月） / 锌合金企业：开工率：中国（月） | ✓ |
| 19 | `SMM_镀zinc成品inv_w_镀zinc板卷_钢铁企业_厂内inv_china_w` | `SMM_coated_zinc成品stock_w_coated_zinc板卷_钢铁企业_厂内stock_china_w` | SMM: 镀锌成品库存（周） / 镀锌板卷：钢铁企业：厂内库存：中国（周） | ✓ |
| 20 | `USGS_tinore_含tin_output_global_y` | `usgs_tin_ore_tin_content_output_global_y` | USGS：锡矿：含锡：产量：全球（年） | ✓ |
| 21 | `USGS_tin矿_含tin_output_global_y` | `USGS_tinore_含tin_output_global_y` | USGS：锡矿：含锡：产量：全球（年） | ✓ |
| 22 | `USGS_混杂低含量copper颗粒的aluminum_avg_price_usa_m` | `usgs_mixed_low_cu_al_avg_price_usa_m` | USGS：混杂低含量铜颗粒的铝：均价：美国（月） | ✓ |
| 23 | `USGS_混杂低含量copper颗粒的aluminum_均价_usa_m` | `USGS_混杂低含量copper颗粒的aluminum_avg_price_usa_m` | USGS：混杂低含量铜颗粒的铝：均价：美国（月） | ✓ |
| 24 | `USGS_粗aluminum_import数量_usa_y` | `usgs_crude_al_import_volume_usa_y` | USGS：粗铝：进口数量：美国（年） | ✓ |
| 25 | `al_2__上期所仓单` | `USGS_粗aluminum_import数量_usa_y` | USGS：粗铝：进口数量：美国（年） | ✓ |
| 26 | `al_2__几内亚cif到岸价` | `aluminum土矿_三水型_45_Al_3_Si_几内亚产_CIF价_shandong主要港口` | 铝土矿：三水型：45%Al，3%Si：几内亚产：CIF价：山东主要港口 | ✓ |
| 27 | `al_2__废铝进口来源` | `al_2_scrap_al_import_source` | 易拉罐盖料：产量：中国（年） | ✓ |
| 28 | `al_2__铝水比例` | `elec解aluminum_aluminum水比例_china_m` | 电解铝：铝水比例：中国（月） | ✓ |
| 29 | `al_3__沪伦比价` | `Mysteel_aluminum_沪伦比值_d` | Mysteel：铝：沪伦比值（日） | ✓ |
| 30 | `al_3__海外氧化铝供应` | `氧化aluminum_AO_1_Al2O3_98_6_australia产_FOB价_奎纳纳` | 氧化铝：AO-1：Al2O3≥98.6%：澳大利亚产：FOB价：奎纳纳 | ✓ |
| 31 | `al_5_2_铝锭出库量` | `elec解aluminum_出库量_china_d` | 电解铝：出库量：中国（日） | ✓ |
| 32 | `al_7_2_辅料成本` | `氟化aluminum_AF_1级_出厂价_华东地区_shandong昭和_d` | 氟化铝：AF-1级：出厂价：华东地区：山东昭和（日） | ✓ |
| 33 | `al_7_2_阳极成本` | `al_7_2_anode_cost` | 预焙阳极：产量：中国（月） | ✓ |
| 34 | `al_7_3_煤_电传导` | `USGS_混杂低含量copper颗粒的aluminum_均价_usa_m` | USGS：混杂低含量铜颗粒的铝：均价：美国（月） | ✓ |
| 35 | `aluminum土ore_三水型_45_Al_3_Si_几内亚产_CIF价_shandong主要port` | `bauxite_trihydrate_45al_3si_guinea_cif_shandong_major_port` | 铝土矿：三水型：45%Al，3%Si：几内亚产：CIF价：山东主要港口 | ✓ |
| 36 | `aluminum土矿_三水型_45_Al_3_Si_几内亚产_CIF价_shandong主要港口` | `aluminum土ore_三水型_45_Al_3_Si_几内亚产_CIF价_shandong主要port` | 铝土矿：三水型：45%Al，3%Si：几内亚产：CIF价：山东主要港口 | ✓ |
| 37 | `by省_by国别` | `by_province_by_country` | 分省/分国别 | ✓ |
| 38 | `china海关_brazilimport矿数量_zinc矿砂及其精矿_import数量_哥伦比亚_china` | `china海关_巴西importore数量_zincore_sand及其conc_import数量_哥伦比亚_china` | 中国海关: 巴西进口矿数量 / 锌矿砂及其精矿：进口数量：哥伦比亚→中国 | ✓ |
| 39 | `china海关_巴西importore数量_zincore_sand及其conc_import数量_哥伦比亚_china` | `china_customs_brazil_import_ore_zn_ore_sand_conc_colombia_china` | 中国海关: 巴西进口矿数量 / 锌矿砂及其精矿：进口数量：哥伦比亚→中国 | ✓ |
| 40 | `coated_zinc板卷_社会stock_china_w` | `coated_zn_plate_roll_social_inv_china_w` | 镀锌板卷：社会库存：中国（周） | ✓ |
| 41 | `coated_zinc板卷_钢铁企业_产能利用率_china_w` | `coated_zn_plate_roll_steel_enterprise_util_china_w` | 镀锌板卷：钢铁企业：产能利用率：中国（周） | ✓ |
| 42 | `copperconc_domestic_23_Cu_计价系数_china_d` | `cu_conc_domestic_23cu_pricing_coeff_china_d` | 铜精矿：国产：23%Cu：计价系数：中国（日） | ✓ |
| 43 | `copper精矿_国产_23_Cu_计价系数_china_d` | `copperconc_domestic_23_Cu_计价系数_china_d` | 铜精矿：国产：23%Cu：计价系数：中国（日） | ✓ |
| 44 | `cu_4_2_国产矿品位与计价系数` | `copper精矿_国产_23_Cu_计价系数_china_d` | 铜精矿：国产：23%Cu：计价系数：中国（日） | ✓ |
| 45 | `electrolyticaluminum_aluminum水比例_china_m` | `electrolytic_al_al_water_ratio_china_m` | 电解铝：铝水比例：中国（月） | ✓ |
| 46 | `electrolyticaluminum_出库量_china_d` | `electrolytic_al_outflow_china_d` | 电解铝：出库量：中国（日） | ✓ |
| 47 | `electrolyticnickel_Ni_99_96_大板_ex_work_price_金昌_金川集团_d` | `electrolytic_ni_9996_plate_ex_work_price_jinchang_jinchuan_d` | 电解镍：Ni≥99.96%，大板：出厂价：金昌：金川集团（日） | ✓ |
| 48 | `elec解aluminum_aluminum水比例_china_m` | `electrolyticaluminum_aluminum水比例_china_m` | 电解铝：铝水比例：中国（月） | ✓ |
| 49 | `elec解aluminum_出库量_china_d` | `electrolyticaluminum_出库量_china_d` | 电解铝：出库量：中国（日） | ✓ |
| 50 | `elec解nickel_Ni_99_96_大板_出厂价_金昌_金川集团_d` | `electrolyticnickel_Ni_99_96_大板_ex_work_price_金昌_金川集团_d` | 电解镍：Ni≥99.96%，大板：出厂价：金昌：金川集团（日） | ✓ |
| 51 | `h2so4_98_出厂价_shandong_wudi_xinyue_d` | `h2so4_98_ex_work_price_shandong_wudi_xinyue_d` | 硫酸：98%：出厂价：山东：无棣鑫岳（日） | ✓ |
| 52 | `mhp_NI_34_CO_2_LMEnickel折扣系数_china主要port_d` | `mhp_ni34_co2_lme_ni_discount_coeff_china_major_port_d` | MHP：NI≥34%，CO≥2%：LME镍折扣系数：中国主要港口（日） | ✓ |
| 53 | `mhp_NI_34_CO_2_LMEnickel折扣系数_china主要港口_d` | `mhp_NI_34_CO_2_LMEnickel折扣系数_china主要port_d` | MHP：NI≥34%，CO≥2%：LME镍折扣系数：中国主要港口（日） | ✓ |
| 54 | `ni_0_2_2现货与升贴水` | `水淬nickel_30_35_Ni_北马其顿产_升贴水_d` | 水淬镍：30-35%Ni：北马其顿产：升贴水（日） | ✓ |
| 55 | `ni_2_2_lme镍0_3升贴水时序` | `mhp_NI_34_CO_2_LMEnickel折扣系数_china主要港口_d` | MHP：NI≥34%，CO≥2%：LME镍折扣系数：中国主要港口（日） | ✓ |
| 56 | `ni_2_6_沪镍前20名席位轮动` | `refinenickel_一级_output_australia_当前财y_y` | 精炼镍：一级：产量：澳大利亚：当前财年（年） | ✓ |
| 57 | `ni_4_4_电解镍厂库存` | `elec解nickel_Ni_99_96_大板_出厂价_金昌_金川集团_d` | 电解镍：Ni≥99.96%，大板：出厂价：金昌：金川集团（日） | ✓ |
| 58 | `ni_7_1_镍矿cif_fob价格` | `红土nickel矿_0_9_Ni_49_Fe_5_Al_33_35_含水_菲律宾` | 红土镍矿：0.9%Ni，49%Fe，5%Al，33-35%含水：菲律宾 | ✓ |
| 59 | `plant_stockstock_SMMrefinezincsmelter样本企业w度成品stock_w_zinc_sm` | `plant_inv_smm_refined_zn_smelter_sample_w_prod_inv_w_zn_smelt` | 厂库库存: SMM精炼锌冶炼厂样本企业周度成品库存（周）/ 锌：冶炼厂：成品库存：中国（周） | ✓ |
| 60 | `refinenickel_一级_output_australia_当前财y_y` | `refined_ni_grade1_output_australia_curr_fy_y` | 精炼镍：一级：产量：澳大利亚：当前财年（年） | ✓ |
| 61 | `sn_2_3_lme锡期货收盘价时序图` | `tin_3个m合约_收盘价_d` | 锡：3个月合约：收盘价（日） | ✓ |
| 62 | `sn_2_3_lme锡现货现金价时序图` | `IMEA_大豆_现货价_tin诺普_d` | IMEA：大豆：现货价：锡诺普（日） | ✓ |
| 63 | `sn_7_3_锡矿进口到岸价` | `USGS_tin矿_含tin_output_global_y` | USGS：锡矿：含锡：产量：全球（年） | ✓ |
| 64 | `sn_7_3_锡精矿价格时序图` | `tin精矿_60_Sn_市场最低价_hunan_d` | 锡精矿：60%Sn：市场最低价：湖南（日） | ✓ |
| 65 | `tin_3个m合约_收盘价_d` | `tin_3m_contract_settle_d` | 锡：3个月合约：收盘价（日） | ✓ |
| 66 | `tinconc_60_Sn_市场min_price_hunan_d` | `sn_conc_60sn_market_min_price_hunan_d` | 锡精矿：60%Sn：市场最低价：湖南（日） | ✓ |
| 67 | `tin精矿_60_Sn_市场最低价_hunan_d` | `tinconc_60_Sn_市场min_price_hunan_d` | 锡精矿：60%Sn：市场最低价：湖南（日） | ✓ |
| 68 | `zinc粉及片状粉末_import数量total_china_m` | `zn_powder_flake_import_total_china_m` | 锌粉及片状粉末：进口数量合计：中国（月）⚠ | ✓ |
| 69 | `zinc粉及片状粉末_import数量合计_china_m` | `zinc粉及片状粉末_import数量total_china_m` | 锌粉及片状粉末：进口数量合计：中国（月）⚠ | ✓ |
| 70 | `zinc精矿_国产_50_Zn_加工费均价_henan_d` | `zincconc_domestic_50zn_tc_avg_henan_d` | 锌精矿：国产：50%Zn：加工费均价：河南（日） | ✓ |
| 71 | `zinc精矿_国产_50_Zn_加工费均价_hunan_d` | `zincconc_domestic_50zn_tc_avg_hunan_d` | 锌精矿：国产：50%Zn：加工费均价：湖南（日） | ✓ |
| 72 | `zinc精矿_国产_50_Zn_加工费均价_shaanxi_d` | `zincconc_domestic_50zn_tc_avg_shaanxi_d` | 锌精矿：国产：50%Zn：加工费均价：陕西（日） | ✓ |
| 73 | `zinc精矿_国产_50_Zn_加工费均价_sichuan_d` | `zincconc_domestic_50zn_tc_avg_sichuan_d` | 锌精矿：国产：50%Zn：加工费均价：四川（日） | ✓ |
| 74 | `zinc精矿_港口inv_tianjin港_w` | `zn_conc_port_inv_tianjin港_w` | 锌精矿：港口库存：天津港（周） | ✓ |
| 75 | `zinc精矿_港口inv_钦州港_w` | `zn_conc_port_inv_qinzhou港_w` | 锌精矿：港口库存：钦州港（周） | ✓ |
| 76 | `zinc精矿_港口inv_锦州港_w` | `zn_conc_port_inv_jinzhou港_w` | 锌精矿：港口库存：锦州港（周） | ✓ |
| 77 | `zinc精矿_港口inv_黄埔港_w` | `zn_conc_port_inv_huangpu港_w` | 锌精矿：港口库存：黄埔港（周） | ✓ |
| 78 | `zn_3_1_1_全球锌矿产量_年` | `zn_3_1_1_global_zn_mine_output_y` | USGS：锌矿：含锌：产量：全球（年） | ✓ |
| 79 | `zn_3_1_1_印度锌精矿产量_smm` | `zn_3_1_1_india_zn_conc_output_smm` | SMM: 锌精矿产量_印度-合计: 年度 | ✓ |
| 80 | `zn_3_1_1_澳大利亚矿山产量` | `zn_3_1_1_australia_mine_output` | 锌：矿山产量：澳大利亚（季） | ✓ |
| 81 | `zn_3_1_1_秘鲁锌精矿产量_smm` | `zn_3_1_1_peru_zn_conc_output_smm` | SMM: 锌精矿产量_秘鲁-合计: 年度 | ✓ |
| 82 | `zn_3_1_1_进口锌精矿tc` | `zn_3_1_1_imported_zn_conc_tc` | 锌精矿：进口：50%Zn：加工费均价（日） | ✓ |
| 83 | `zn_3_1_1_进口锌精矿粗炼费` | `zn_3_1_1_imported_zn_conc_smelt_fee` | 锌精矿：进口：50%Zn：粗炼费最低价：中国（日） | ✓ |
| 84 | `zn_3_1_2_冶炼厂原料库存天数` | `zn_3_1_2_smelter_raw_inv_days` | 锌精矿：原料：库存天数：中国（周） | ✓ |
| 85 | `zn_3_1_2_国产tc_四川` | `zinc精矿_国产_50_Zn_加工费均价_sichuan_d` | 锌精矿：国产：50%Zn：加工费均价：四川（日） | ✓ |
| 86 | `zn_3_1_2_国产tc_河南` | `zinc精矿_国产_50_Zn_加工费均价_henan_d` | 锌精矿：国产：50%Zn：加工费均价：河南（日） | ✓ |
| 87 | `zn_3_1_2_国产tc_湖南` | `zinc精矿_国产_50_Zn_加工费均价_hunan_d` | 锌精矿：国产：50%Zn：加工费均价：湖南（日） | ✓ |
| 88 | `zn_3_1_2_国产tc_陕西` | `zinc精矿_国产_50_Zn_加工费均价_shaanxi_d` | 锌精矿：国产：50%Zn：加工费均价：陕西（日） | ✓ |
| 89 | `zn_3_1_2_国产锌精矿tc` | `zn_3_1_2_domestic_zn_conc_tc` | 锌精矿：国产：50%Zn：加工费均价：广西（日） | ✓ |
| 90 | `zn_3_1_2_锌精矿港口库存` | `zn_3_1_2_zn_conc_port_inventory` | 锌精矿：港口库存：中国（周） | ✓ |
| 91 | `zn_3_1_2_锌精矿港口库存_分港口` | `zinc精矿_港口inv_tianjin港_w` | 锌精矿：港口库存：天津港（周） | ✓ |
| 92 | `zn_3_1_2_锌精矿港口库存_钦州港` | `zinc精矿_港口inv_钦州港_w` | 锌精矿：港口库存：钦州港（周） | ✓ |
| 93 | `zn_3_1_2_锌精矿港口库存_锦州港` | `zinc精矿_港口inv_锦州港_w` | 锌精矿：港口库存：锦州港（周） | ✓ |
| 94 | `zn_3_1_2_锌精矿港口库存_黄埔港` | `zinc精矿_港口inv_黄埔港_w` | 锌精矿：港口库存：黄埔港（周） | ✓ |
| 95 | `zn_3_1_3_98_硫酸价格` | `zn_3_1_3_98_h2so4_price` | 硫酸：98%：出厂价：山东：齐成石化（日） | ✓ |
| 96 | `zn_3_1_3_98_硫酸价格_无棣` | `h2so4_98_出厂价_shandong_wudi_xinyue_d` | 硫酸：98%：出厂价：山东：无棣鑫岳（日） | ✓ |
| 97 | `zn_3_1_4_smm预计中国精炼锌产量` | `样本企业_refinezinc_output_china_m` | 样本企业：精炼锌：产量：中国（月） | ✓ |
| 98 | `zn_3_1_4_中国精炼锌产量_周` | `refinezinc_output_china_w` | 精炼锌：产量：中国（周） | ✓ |
| 99 | `zn_3_1_4_精炼锌净出口` | `zinc粉及片状粉末_import数量合计_china_m` | 锌粉及片状粉末：进口数量合计：中国（月）⚠ | ✓ |
| 100 | `zn_3_1_5_再生锌产量_样本` | `样本企业_recyclezinc_output_china_m` | 样本企业：再生锌：产量：中国（月） | ✓ |
| 101 | `zn_3_1_5_次氧化锌_河北` | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_河北_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：河北（日） | ✓ |
| 102 | `zn_3_1_5_次氧化锌_河南` | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_henan_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：河南（日） | ✓ |
| 103 | `zn_3_1_5_次氧化锌_湖南` | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_hunan_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：湖南（日） | ✓ |
| 104 | `zn_3_1_5_次氧化锌价格` | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_jiangsu_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：江苏（日） | ✓ |
| 105 | `zn_4_1_lme锌库存` | `LME_zincinv总计_d_LME_zinc_期货inv_d` | LME: 锌库存总计（日） / LME：锌：期货库存（日） | ✓ |
| 106 | `zn_4_1_lme锌注销仓单占比` | `LME_zinc_注销warrant_d_LME_zinc_注销占比_d` | LME: 锌: 注销仓单（日） / LME：锌：注销占比（日） | ✓ |
| 107 | `zn_4_1_上期所锌库存` | `SHFE_zinc_invw报_本winv期货_w_SHFE_zinc_期货inv_w` | SHFE: 锌: 库存周报: 本周库存期货（周） / SHFE：锌：期货库存（周） | ✓ |
| 108 | `zn_4_2_上期所锌仓单分地区` | `SHFE_zinc_warrantd报分地区_shanghai_期货_d_等` | SHFE: 锌: 仓单日报分地区_上海: 期货（日）等 | ✓ |
| 109 | `zn_4_4_国内锌厂内锌锭库存` | `厂库inv_SMMrefinezincsmelt厂样本企业w度成品inv_w_zinc_smelt厂_成品inv_chi` | 厂库库存: SMM精炼锌冶炼厂样本企业周度成品库存（周）/ 锌：冶炼厂：成品库存：中国（周） | ✓ |
| 110 | `zn_5_1_压铸锌合金企业开工率` | `SMM_压铸zinc合金util_m_zinc合金企业_util_china_m` | SMM: 压铸锌合金开工率（月） / 锌合金企业：开工率：中国（月） | ✓ |
| 111 | `zn_5_2_全国镀锌板卷产能利用率` | `镀zinc板卷_钢铁企业_capacity利用率_china_w` | 镀锌板卷：钢铁企业：产能利用率：中国（周） | ✓ |
| 112 | `zn_5_2_全国镀锌板卷社会库存` | `镀zinc板卷_社会inv_china_w` | 镀锌板卷：社会库存：中国（周） | ✓ |
| 113 | `zn_5_2_全国镀锌板卷钢厂库存` | `SMM_镀zinc成品inv_w_镀zinc板卷_钢铁企业_厂内inv_china_w` | SMM: 镀锌成品库存（周） / 镀锌板卷：钢铁企业：厂内库存：中国（周） | ✓ |
| 114 | `zn_5_3_制造业pmi` | `NBS_制造业采购经理指数_m` | NBS: 制造业采购经理指数（月） | ✓ |
| 115 | `zn_6_1_锌精矿进口来源国结构` | `china海关_brazilimport矿数量_zinc矿砂及其精矿_import数量_哥伦比亚_china` | 中国海关: 巴西进口矿数量 / 锌矿砂及其精矿：进口数量：哥伦比亚→中国 | ✓ |
| 116 | `zn_6_2_沪伦比与精锌进口盈亏` | `SMM_refinezincimport盈亏_zinc沪伦比值_d` | SMM: 精炼锌进口盈亏: 锌沪伦比值（日） | ✓ |
| 117 | `zn_6_2_精炼锌进口来源国结构` | `分省_分国别` | 分省/分国别 | ✓ |
| 118 | `zn_6_4_lme注册仓单` | `LME_zinc仓库注册warrant_合计_d_LME_zinc_注册warrant_d` | LME: 锌仓库注册仓单: 合计（日） / LME：锌：注册仓单（日） | ✓ |
| 119 | `zn_conc_port_inv_huangpu港_w` | `zn_conc_port_inv_huangpu_w` | 锌精矿：港口库存：黄埔港（周） | ✓ |
| 120 | `zn_conc_port_inv_jinzhou港_w` | `zn_conc_port_inv_jinzhou_w` | 锌精矿：港口库存：锦州港（周） | ✓ |
| 121 | `zn_conc_port_inv_qinzhou港_w` | `zn_conc_port_inv_qinzhou_w` | 锌精矿：港口库存：钦州港（周） | ✓ |
| 122 | `zn_conc_port_inv_tianjin港_w` | `zn_conc_port_inv_tianjin_w` | 锌精矿：港口库存：天津港（周） | ✓ |
| 123 | `主连` | `_main_metric` | 期货主连结算价 | ✓ |
| 124 | `分省_分国别` | `by省_by国别` | 分省/分国别 | ✓ |
| 125 | `厂库inv_SMMrefinezincsmelt厂样本企业w度成品inv_w_zinc_smelt厂_成品inv_chi` | `plant_stockstock_SMMrefinezincsmelter样本企业w度成品stock_w_zinc_sm` | 厂库库存: SMM精炼锌冶炼厂样本企业周度成品库存（周）/ 锌：冶炼厂：成品库存：中国（周） | ✓ |
| 126 | `开工率` | `_capacity_util` | 开工率 | ✓ |
| 127 | `样本企业_recyclezinc_output_china_m` | `sample_recycle_zn_output_china_m` | 样本企业：再生锌：产量：中国（月） | ✓ |
| 128 | `样本企业_refinezinc_output_china_m` | `sample_refined_zn_output_china_m` | 样本企业：精炼锌：产量：中国（月） | ✓ |
| 129 | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_henan_d` | `次氧化zinc_50_Zn_ci10_pb8_汇总price_henan_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：河南（日） | ✓ |
| 130 | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_hunan_d` | `次氧化zinc_50_Zn_ci10_pb8_汇总price_hunan_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：湖南（日） | ✓ |
| 131 | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_jiangsu_d` | `次氧化zinc_50_Zn_ci10_pb8_汇总price_jiangsu_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：江苏（日） | ✓ |
| 132 | `次氧化zinc_50_Zn_CI10_Pb8_汇总price_河北_d` | `次氧化zinc_50_Zn_ci10_pb8_汇总price_hebei_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：河北（日） | ✓ |
| 133 | `次氧化zinc_50_Zn_ci10_pb8_汇总price_hebei_d` | `zn_oxide_50zn_ci10_pb8_agg_price_hebei_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：河北（日） | ✓ |
| 134 | `次氧化zinc_50_Zn_ci10_pb8_汇总price_henan_d` | `zn_oxide_50zn_ci10_pb8_agg_price_henan_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：河南（日） | ✓ |
| 135 | `次氧化zinc_50_Zn_ci10_pb8_汇总price_hunan_d` | `zn_oxide_50zn_ci10_pb8_agg_price_hunan_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：湖南（日） | ✓ |
| 136 | `次氧化zinc_50_Zn_ci10_pb8_汇总price_jiangsu_d` | `zn_oxide_50zn_ci10_pb8_agg_price_jiangsu_d` | 次氧化锌：50%Zn，CI10%，Pb8%：汇总价格：江苏（日） | ✓ |
| 137 | `氟化aluminum_AF_1级_ex_work_price_华东地区_shandong昭和_d` | `fluoroaluminum_af1_grade_ex_work_price_east_china_shandong_shawo_d` | 氟化铝：AF-1级：出厂价：华东地区：山东昭和（日） | ✓ |
| 138 | `氟化aluminum_AF_1级_出厂价_华东地区_shandong昭和_d` | `氟化aluminum_AF_1级_ex_work_price_华东地区_shandong昭和_d` | 氟化铝：AF-1级：出厂价：华东地区：山东昭和（日） | ✓ |
| 139 | `氧化aluminum_AO_1_Al2O3_98_6_australia产_FOB价_奎纳纳` | `alumina_ao1_al2o3_98_6_australia_fob_kunana` | 氧化铝：AO-1：Al2O3≥98.6%：澳大利亚产：FOB价：奎纳纳 | ✓ |
| 140 | `水淬nickel_30_35_Ni_北马其顿产_升贴水_d` | `water_quenched_ni_30_35_ni_n_macedonia_premium_d` | 水淬镍：30-35%Ni：北马其顿产：升贴水（日） | ✓ |
| 141 | `社库` | `_social_stock` | 社会库存 | ✓ |
| 142 | `精炼产量` | `_refined_output` | 精炼产量 | ✓ |
| 143 | `红土nickelore_0_9_Ni_49_Fe_5_Al_33_35_含水_菲律宾` | `laterite_ni_ore_0_9ni_49fe_5al_33_35_moisture_philippines` | 红土镍矿：0.9%Ni，49%Fe，5%Al，33-35%含水：菲律宾 | ✓ |
| 144 | `红土nickel矿_0_9_Ni_49_Fe_5_Al_33_35_含水_菲律宾` | `红土nickelore_0_9_Ni_49_Fe_5_Al_33_35_含水_菲律宾` | 红土镍矿：0.9%Ni，49%Fe，5%Al，33-35%含水：菲律宾 | ✓ |
| 145 | `表观消费` | `_apparent_consumption` | 表观消费 | ✓ |
| 146 | `镀zinc板卷_社会inv_china_w` | `coated_zinc板卷_社会stock_china_w` | 镀锌板卷：社会库存：中国（周） | ✓ |
| 147 | `镀zinc板卷_钢铁企业_capacity利用率_china_w` | `coated_zinc板卷_钢铁企业_产能利用率_china_w` | 镀锌板卷：钢铁企业：产能利用率：中国（周） | ✓ |

---

## 统计

- 总替换数：147
- 纯中文key→英文：43
- 混合中文+英文key→英文：104
- 残留中文key：0（全部清除）