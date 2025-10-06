from .base import TL1BaseCommand, TL1BaseResponse
from typing import List, Optional, Literal, ClassVar, Dict, Any, Type

class OcrsResponse(TL1BaseResponse):
    def rename_positional_params(
        self, parsed_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for record in parsed_data:
            record["FROMAID"] = record.pop("positional_param_0_0")
            record["TOAID"] = record.pop("positional_param_0_1")
            record["CrossConnectType"] = record.pop("positional_param_1_0")
            record["OPERSTATE"] = record.pop("positional_param_3_0")
            # record["SUBOPERSTATE"] = record.pop("positional_param_3_1")
            pass
        return parsed_data

class RetrieveOcrs(TL1BaseCommand):
    help_text: ClassVar[str] = "RTRV-OCRS:[<TID>]:[<FROMAID>,<TOAID>]:<CTAG>:::[<CHANPLANTYPE=CUSTOM-CHPLAN-1|FLEX-CHPLAN-1|FLEX-CHPLAN-2|FLEX-CHPLAN-3|FLEX-CHPLAN-4|OCG-CHPLAN-1|OCG-CHPLAN-2|DEFAULT-CHPLAN-AOFX>][,<SIGTYPE=SIGNALED|MANUAL>][,<OELAID=oelaid>]:"
    verb: ClassVar[str] = "RTRV"
    modifier: ClassVar[str] = "OCRS"
    response_class: ClassVar[Type[TL1BaseResponse]] = OcrsResponse
    
    fromaid: Optional[str] = None
    toaid: Optional[str] = None
    chanplantype: Optional[Literal['CUSTOM-CHPLAN-1', 'FLEX-CHPLAN-1', 'FLEX-CHPLAN-2', 'FLEX-CHPLAN-3', 'FLEX-CHPLAN-4', 'OCG-CHPLAN-1', 'OCG-CHPLAN-2', 'DEFAULT-CHPLAN-AOFX']] = None
    sigtype: Optional[Literal['SIGNALED', 'MANUAL']] = None
    oelaid: Optional[str] = None

class EnterOcrs(TL1BaseCommand):
    help_text: ClassVar[str] = "ENT-OCRS:[<TID>]:<FROMAID>,<TOAID>:<CTAG>:::[<LABEL=label>,][<SUPCHNUM=supchnum>,][<CKTIDSUFFIX=cktidsuffix>,]<FREQSLOTPLANTYPE=freqslotplantype>[,<OELAID=oelaid>][,<SCHOFFSET=schoffset>][,<FREQSLOTLIST=freqslotlist>][,<POSSIBLEFREQSLOTLIST=possiblefreqslotlist>][,<LMSCH=lmsch>][,<PASSBANDLIST=passbandlist>][,<CARRIERLIST=carrierlist>][,<POSSIBLEPASSBANDLIST=possiblepassbandlist>][,<BAUDRATE=NA|16G|17G|22G|33G>][,<RXSCHOFFSET=rxschoffset>][,<AUTORETUNELMSCH=ENABLED|DISABLED>][,<MODULATIONCAT=NA|16G|17G-DAC|17G-DAC-12GOFFSET|22G-DAC|22G-DAC-12GOFFSET|33G-DAC|33G-DAC-12GOFFSET>][,<PROFSCHNUM=profschnum>][,<SCHPROFID=schprofid>][,<SCHTHPROFLIST=schthproflist>][,<PGAID=pgaid>][,<INTRACARRSPECSHAPING=ENABLED|DISABLED>]"
    verb: ClassVar[str] = "ENT"
    modifier: ClassVar[str] = "OCRS"
    fromaid: str
    toaid: str
    label: Optional[str] = None
    supchnum: Optional[str] = None
    cktidsuffix: Optional[str] = None
    freqslotplantype: str
    oelaid: Optional[str] = None
    schoffset: Optional[str] = None
    freqslotlist: Optional[List[str]] = None
    possiblefreqslotlist: Optional[List[str]] = None
    lmsch: Optional[str] = None
    passbandlist: Optional[List[str|int]] = None
    carrierlist: Optional[List[str|int]] = None
    possiblepassbandlist: Optional[List[str]] = None
    baudrate: Optional[Literal['NA', '16G', '17G', '22G', '33G']] = None
    rxschoffset: Optional[str] = None
    autoretunelmsch: Optional[Literal['ENABLED', 'DISABLED']] = None
    modulationcat: Optional[Literal['NA', '16G', '17G-DAC', '17G-DAC-12GOFFSET', '22G-DAC', '22G-DAC-12GOFFSET', '33G-DAC', '33G-DAC-12GOFFSET']] = None
    profschnum: Optional[str] = None
    schprofid: Optional[str] = None
    schthproflist: Optional[List[str]] = None
    pgaid: Optional[str] = None
    intracarrspecshaping: Optional[Literal['ENABLED', 'DISABLED']] = None

class EditOcrs(TL1BaseCommand):
    help_text: ClassVar[str] = "ED-OCRS:[<TID>]:<FROMAID>,<TOAID>:<CTAG>:::[<LABEL=label>][,<CKTIDSUFFIX=cktidsuffix>][,<FREQSLOTLIST=freqslotlist>][,<POSSIBLEFREQSLOTLIST=possiblefreqslotlist>][,<LMSCH=lmsch>][,<PASSBANDLIST=passbandlist>][,<CARRIERLIST=carrierlist>][,<POSSIBLEPASSBANDLIST=possiblepassbandlist>][,<ACTIVEPASSBANDLIST=activepassbandlist>][,<RXSCHOFFSET=rxschoffset>][,<AUTORETUNELMSCH=ENABLED|DISABLED>][,<SCHTHPROFLIST=schthproflist>][,<INTRACARRSPECSHAPING=ENABLED|DISABLED>]"
    verb: ClassVar[str] = "ED"
    modifier: ClassVar[str] = "OCRS"
    fromaid: str
    toaid: str
    label: Optional[str] = None
    cktidsuffix: Optional[str] = None
    freqslotlist: Optional[List[str]] = None
    possiblefreqslotlist: Optional[List[str]] = None
    lmsch: Optional[str] = None
    passbandlist: Optional[List[str]] = None
    carrierlist: Optional[List[str]] = None
    possiblepassbandlist: Optional[List[str]] = None
    activepassbandlist: Optional[List[str]] = None
    rxschoffset: Optional[str] = None
    autoretunelmsch: Optional[Literal['ENABLED', 'DISABLED']] = None
    schthproflist: Optional[List[str]] = None
    intracarrspecshaping: Optional[Literal['ENABLED', 'DISABLED']] = None

class DeleteOcrs(TL1BaseCommand):
    help_text: ClassVar[str] = "DLT-OCRS:[<TID>]:<FROMAID>,<TOAID>:<CTAG>::"
    verb: ClassVar[str] = "DLT"
    modifier: ClassVar[str] = "OCRS"
    fromaid: str
    toaid: str