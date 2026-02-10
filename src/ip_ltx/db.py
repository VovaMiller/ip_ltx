

class addon_flags:
    scope    = 1
    launcher = 2
    silencer = 4


class object_flags:
    flUseSwitches       = 1     # 0x00000001
    flSwitchOnline      = 2     # 0x00000002
    flSwitchOffline     = 4     # 0x00000004
    flInteractive       = 8     # 0x00000008

    flVisibleForAI      = 16    # 0x00000010
    flUsefulForAI       = 32    # 0x00000020
    flOfflineNoMove     = 64    # 0x00000040
    flUsedAI_Locations  = 128   # 0x00000080

    flUseGroupBehaviour = 256   # 0x00000100
    flCanSave           = 512   # 0x00000200
    flVisibleForMap     = 1024  # 0x00000400
    flUseSmartTerrains  = 2048  # 0x00000800

    flCheckForSeparator = 4096  # 0x00001000
    flCorpseRemoval     = 8192  # 0x00002000
