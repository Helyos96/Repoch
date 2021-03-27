# Utility to convert monobehaviours from asset files to json.
# Requires a type tree file generated with TypeTreeGenerator.exe (UABE)

import sys
import Dumper

if len(sys.argv) <= 3:
	print("Usage: " + sys.argv[0] + " <type_tree_file> <asset_folder> <output_folder>")
	sys.exit()

assetfiles = ["globalgamemanagers.assets", "resources.assets", "sharedassets0.assets"]
# Blacklist applies to both root nodes and pptr nodes
blacklist = ["UMAAssetIndexer", "SlotDataAsset", "CachedPrefab", "OverlayDataAsset", "UMAWardrobeRecipe", "AbilityObjectConstructor", "AnimationFMODSoundPlayer", "AlwaysFaceCamera", "DynamicDNAConverterBehaviour", "UMAExpressionSet", "UmaTPose", "UsingMultipleAbilitiesAI", "VerticalLayoutGroup", "VoidMaterialComponent", "Waiting", "WalkAnimationScaler", "WhenStunVFXPlayer", "WorldAreaEnterListener", "TargetFinder", "StateSoundManager", "ActorDisplayInformation", "ActorSync", "RelayDamageEvents", "RagdollController", "BlendModeEffect", "ActorVisuals", "DetachParticleSystemsOnDeath", "UMABonePose", "Stunned", "AnimationSoundBehaviour", "RandomIdle", "MeshData", "ClothData", "RectangleSpawner", "PrefabReference", "AbilityObjectIndicator", "HitSoundReceiver", "Prefabs", "FT_DestroyParticleByDuration", "MovingToTarget", "RendererManager", "PlayOneShotSound", "StartsTowardsTarget", "AilmentVFXCreator", "CreationReferences", "IMAttacher", "AnimationSpeedRandomiser", "Image", "Button", "ButtonSounds", "HitParticleEffect", "HitFlash", "Mask", "RFX4_ShaderFloatCurve", "TextMeshProUGUI", "DestroyAfterDuration", "ComplexAnimationManager", "AlignmentManager", "ActorPointerEventListener", "ActorOutlineVFX", "CollisionAndNavMeshToggler", "ConstantRotation", "DOTweenAnimation", "Dying", "FX_RandomScale", "FX_Rotation", "LayoutElement", "Outline", "PeriodicallyFadeImage", "PlaySoundDuringLifetime", "SpeedManager", "ConditionHandler", "CharacterStatusTracker", "CharacterStatDisplay", "HitVfxPool", "HorizontalLayoutGroup", "ScaleProjectorOrthographicSizeWithLossyScale", "StartsAtTarget", "AbilityMover", "HitDetector", "SelfDestroyer", "DestroyOnInanimateCollison", "DestroyOnFailingToPierceEnemy", "ShakeScreenOnHit", "HitSoundEmitter", "CreateOnDeath", "LocationDetector", "AttachToAllyOnCreation", "BuffParent", "DestroySelfOnParentDeath", "MoveToParentColliderCentre", "ResizeBasedOnParentCollider", "CreateAbilityObjectOnDeath", "DefineStartDirection", "StartsAboveTarget", "DestroyAfterDurationAfterReachingTargetLocation", "CreateAtTargetLocationOnCreation", "StopAtTargetLocation", "ShakeScreenOnDeath", "SummonEntityOnDeath", "ColliderChanger", "ShakeScreenOnStart", "CreateGlobalOnDeath", "AttachToCreatorOnCreation", "AttachToNearestEnemyOnCreation", "MoveToNearestEnemyOnCreation", "AttachToPlayer", "ActivateCollidersOnStart", "RaycastAbilityMover", "AbilityParabolicMovement", "RandomiseTargetLocation", "BeamColliderScaler", "FadeParticlesWhenDurationIsLow", "DisableActorsOfTypeInteraction", "RicochetMovement", "TimerListener", "MoveToNearestMinion", "StartAwayFromTarget", "HomingMovement", "ChangeColliderSizeOverTime", "AbilityEventListener", "RotateAroundUp", "DestroyOnParentReachingAbilityMovementDestination", "EquipTypeAngles", "FootstepRaycastTrigger", "IMSlotManager", "PlayerAnimationManager", "PlayerFootstepSoundEmitter"]
# Whitelist, if not empty, applies only to root nodes (file dumps)
whitelist = []
#whitelist = ["Ability", "AbilityManager", "AffixList", "GlobalTreeData", "ItemList", "PropertyList", "UniqueList", "WarpathTree", "SkillTreeNode", "CharacterClassList", "KnightTree"]
# Some monobehaviours start at a weird raw position which can't be guessed currently
seek_override = {"SkillTreeNode": 0x2C}
# For classes that are parsed as pptrs (subnodes), only keep some of the fields
pptr_override = {"Ability":   ["abilityName", "playerAbilityID"],
				 "Quest":     ["id"],
				 "Objective": ["id"]}
d = Dumper.Dumper(sys.argv[1], sys.argv[2], assetfiles, seek_override, blacklist = blacklist, whitelist = whitelist, pptr_override = pptr_override)
# Passing in ignore_pptr = False is slower but will resolve some of the files' interlinks
d.dump_all_json(sys.argv[3], ignore_pptr = False)
