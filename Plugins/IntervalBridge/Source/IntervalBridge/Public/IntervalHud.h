// Copyright interval.
//
// THE TWO THINGS THAT ARE ALWAYS ON SCREEN.
//
// CHAT, BECAUSE CHAT IS THE POINT OF THE WORLD.
//
// The world's rhythm was designed around people talking to each other: a tick
// a second, walks that take minutes, crops that take twelve, so that there is
// always room to write to somebody. In the user's words -- "chat is basically
// the most important thing in this world/game. I've designed everything to
// revolve around schelling points and actions occurring in a way that makes
// time for the player to write to strangers/friends while playing."
//
// Which settles where it lives. Not behind a key: "so the player does not
// forget it exists". A chat behind a keypress is a chat nobody opens, and a
// world whose whole tempo was built to leave room for conversation fails
// quietly if the window hides the conversation. It is up, always, with its
// input line ready.
//
// THE PACK, BECAUSE IT IS READ WHILE DOING SOMETHING ELSE.
//
// "I don't think someone should have to open a menu to see how many free slots
// they have left when chopping a tree." Anything a citizen needs WHILE acting
// has to be readable without an action, because the action is the thing they
// are already doing. So the pack is a grid of real slots -- countable at a
// glance, empty ones visibly empty -- and not the list of type it was.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "IntervalTypes.h"
#include "IntervalHud.generated.h"

class UBorder;
class UHorizontalBox;
class UImage;
class UEditableTextBox;
class UScrollBox;
class UTextBlock;
class UUniformGridPanel;
class UVerticalBox;
class AIntervalHand;
class UIntervalBridgeSubsystem;

/** One pack slot: a box that is either empty or holds a thing. */
UCLASS()
class INTERVALBRIDGE_API UIntervalSlotWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	void Show(const FString& InItem, int32 InQty);

	virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry,
		const FPointerEvent& Event) override;

	/** The sprite for an item, or null when none has been rendered. */
	static UTexture2D* IconFor(const FString& Which);

	UPROPERTY() int32 Index = 0;
	UPROPERTY() FString Item;
	UPROPERTY() int32 Qty = 0;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;
	UPROPERTY() TObjectPtr<UIntervalBridgeSubsystem> Bridge;

	/**
	 * WHICH GRID THIS CELL BELONGS TO: the pack, or the vault at the counter.
	 *
	 * The same widget draws both, deliberately. A bank screen with its own
	 * cells, its own sprites and its own idea of what a stack looks like is a
	 * second visual language for the same idea, and the interface has one --
	 * so the vault is the pack's grid, in the pack's plate, with the pack's
	 * left-click-does-the-obvious-thing and right-click-says-everything.
	 */
	UPROPERTY() bool bIsVault = false;

	UFUNCTION()
	void Picked();

private:
	UPROPERTY() TObjectPtr<UBorder> Cell;
	UPROPERTY() TObjectPtr<class UImage> Sprite;
	UPROPERTY() TObjectPtr<UTextBlock> Name;
	UPROPERTY() TObjectPtr<UTextBlock> Count;
};

/**
 * ONE OF THE THREE DOORS ABOVE THE PACK.
 *
 * Everything a citizen knows about themselves -- what they are wearing, what
 * they have learned, what they can cast -- was on a grey overlay in the corner
 * of the screen that could not be clicked and never went away. It is behind
 * these instead: "magic spellbook, equipment and character info/skills should
 * be available as clickable buttons above the inventory, that when clicked,
 * brings up menu with respective options/info."
 *
 * They sit directly over the pack because that is where a player's eye already
 * is, and they are icons rather than words for the same reason the slots are
 * sprites: a row of three short words reads as a sentence and has to be
 * parsed, a row of three pictures does not.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalTabWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	/** 0 equipment, 1 the citizen, 2 the book. */
	UPROPERTY() int32 Which = 0;
	UPROPERTY() FString Icon;
	UPROPERTY() FString Title;
	UPROPERTY() TObjectPtr<class UIntervalHudWidget> Owner;

	void Light(bool bOpen);

	UFUNCTION()
	void Hit();

private:
	UPROPERTY() TObjectPtr<UBorder> Face;
	UPROPERTY() TObjectPtr<UImage> Mark;
};

/** One castable word in the book. */
UCLASS()
class INTERVALBRIDGE_API UIntervalSpellRow : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	UPROPERTY() FString Spell;
	UPROPERTY() bool bKnown = false;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;

	/**
	 * NOT EVERY LINE IN A BOOK IS A SPELL.
	 *
	 * `invoke` presses three magic-stones into a sigil. It is the one act in
	 * the book that takes no words and no target -- it is a thing you DO with
	 * what you are carrying -- and it had no row because the book only knew
	 * how to list words. An empty verb means the line speaks its spell, which
	 * is what every row did before there was a second kind.
	 */
	UPROPERTY() FString Verb;
	UPROPERTY() FString Label;
	/** The sheet this row belongs to, for the one line that is a setting. */
	UPROPERTY() TObjectPtr<class UIntervalHudWidget> Hud;
	/** Who the deed is about, for the rows that are about the citizen. */
	UPROPERTY() FIntervalTarget On;

	UFUNCTION()
	void Speak();
};

/**
 * ONE THING A CITIZEN IS WEARING, AND A WAY TO TAKE IT OFF.
 *
 * `unwield` had no door. It is in the pack's menu under anything equippable,
 * and that line has never worked: a pack row files `slot`, a number, and
 * `unwield` is `{ gear }`, a WORD -- `weapon`, `head`. So the deed was
 * malformed before the world ever judged it, and a citizen who put a helmet
 * on could not take it off through the window at all. The verb counted as
 * reachable in every coverage report because the line was there to see.
 *
 * The worn sheet already lists what is on: this makes each of those lines a
 * thing you can click. One option, so a left click does it, which is the same
 * arrangement the pack has for a loaf -- see the note on UIntervalSlotWidget.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalWornRow : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;

	/** The slot's own word, which is what the deed carries. */
	UPROPERTY() FString Gear;
	/** What is in it, or empty for a slot with nothing in it. */
	UPROPERTY() FString Item;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;

	UFUNCTION()
	void Take();
};

/**
 * THE MINIMAP, AND WHY A WINDOW LIKE THIS CANNOT DO WITHOUT ONE.
 *
 * The camera sees about a dozen tiles, so a click can only ever ask for a walk
 * of about six. The island is nine hundred tiles across and its settlements
 * are sixty to three hundred apart: crossing it by clicking the edge of the
 * view is fifty clicks of watching a citizen shuffle, and picking a way round
 * a building you cannot see the end of is guesswork. That is not a hard
 * journey, it is a tedious one, and it was the single biggest thing standing
 * between this window and being playable.
 *
 * Asked for in exactly those terms: "maybe we should add a minimap you can
 * click on to walk more steps without constantly clicking right in front of
 * you."
 *
 * It is a picture of what the window ALREADY KNOWS -- the terrain codes of the
 * chunks it has drawn, and the nodes, beasts and citizens in the frame. It
 * invents no knowledge: a tile whose chunk has not arrived is left blank
 * rather than guessed at, which is also an honest drawing of how far a citizen
 * can see.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalMapWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry,
		const FPointerEvent& Event) override;

	UPROPERTY() TObjectPtr<UIntervalBridgeSubsystem> Bridge;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;
	/** What this citizen has seen of the island, kept between sessions. */
	UPROPERTY() TObjectPtr<class UIntervalMemorySubsystem> Memory;

	/**
	 * Tiles each way from the citizen. The picture is twice this plus one.
	 *
	 * FIFTY-SIX WAS TOO FAR OUT. A hundred and thirteen tiles across a disc
	 * two hundred pixels wide is under two pixels a tile, so a whole cottage
	 * was seven pixels and a doorway was one -- and the minimap is precisely
	 * where a citizen has to aim when a roof is between the camera and the
	 * floor they want to stand on: "when in a town it should be easy to click
	 * the minimap to enter a building before you can click inside on the
	 * screen (because of the roof)".
	 *
	 * Twenty-four is forty-nine tiles across, a little over four pixels each,
	 * which makes a building a block you can hit and still shows the whole of
	 * a small town. It is the one number the whole picture is drawn from, so
	 * moving it is the whole of the zoom.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hud")
	int32 Reach = 24;

private:
	void Repaint();

	UPROPERTY() TObjectPtr<class UImage> Face;
	UPROPERTY() TObjectPtr<UTexture2D> Canvas;
	UPROPERTY() TObjectPtr<class AIntervalGround> Land;
	TArray<FColor> Pixels;
	/** The four cardinal letters, swung round the rim as the camera turns. */
	UPROPERTY() TObjectPtr<class UTextBlock> Points[4];
	/** The yaw the picture was last drawn with; a click is read back by it. */
	float MapYaw = 0.f;
	int64 LastPainted = -1;
};

/**
 * THE WHOLE ISLAND, as much of it as this citizen has walked.
 *
 * The minimap is a hundred tiles of ground around your feet. This is the other
 * end of the same record: every tile the window has ever drawn for this
 * citizen, at one pixel a tile, with the ground they have never been to left
 * dark. It is not a map handed out at birth -- this world has no satellites,
 * it has people who walk -- so what it draws is a portrait of where somebody
 * has been as much as it is a chart of where things are.
 *
 * NORTH-UP, and deliberately unlike the minimap. The minimap turns with the
 * camera because its job is "what is in front of me"; a world map's job is
 * "where is Thornbury from here", and that question has one answer that does
 * not depend on which way you happen to be facing.
 */
UCLASS()
class INTERVALBRIDGE_API UIntervalWorldMapWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& Geometry,
		const FPointerEvent& Event) override;

	UPROPERTY() TObjectPtr<UIntervalBridgeSubsystem> Bridge;
	UPROPERTY() TObjectPtr<class UIntervalMemorySubsystem> Memory;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;

private:
	void Repaint();

	UPROPERTY() TObjectPtr<class UImage> Face;
	UPROPERTY() TObjectPtr<UTextBlock> Caption;
	UPROPERTY() TObjectPtr<UTexture2D> Canvas;
	UPROPERTY() TObjectPtr<class UCanvasPanel> Over;
	/** Sized to the island, so canvas units are tile coordinates. */
	UPROPERTY() TObjectPtr<class USizeBox> Shape;
	UPROPERTY() TArray<TObjectPtr<UTextBlock>> Signs;
	TArray<FColor> Pixels;
	double PaintedAt = 0.0;
};

UCLASS()
class INTERVALBRIDGE_API UIntervalHudWidget : public UUserWidget
{
	GENERATED_BODY()

public:

	/**
	 * WHETHER THIS PLAYER WANTS THE WORLD'S OWN HOURS.
	 *
	 * The island runs a day and a night and the night is genuinely dark, which
	 * is the right drawing of a world where a watchfire means something -- and
	 * it is also an hour of somebody's ninety-minute day spent squinting:
	 * "we should probably make the day cycle optional too, so if a player
	 * wants they can just have daylight the entire time".
	 *
	 * It changes NOTHING but pixels. The world's hour is still what every
	 * other window sees, no deed is sent, and the frames say what they said --
	 * which is exactly the licence `ForceDay` was written under.
	 */
	UFUNCTION() void TurnTheSun();

	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& Geometry, float DeltaSeconds) override;

	UFUNCTION()
	void Heard(const FIntervalSaid& Said);

	/**
	 * §9f: A THING THE WORLD CRIED, which has no speaker and is not chat.
	 *
	 * It goes in the same column, because that is where a reader is already
	 * looking and a second place to look is a place nobody looks. It is set
	 * apart by weight rather than by position: the world's own gold, italic,
	 * and no name in front of it, so a cry is never mistaken for somebody
	 * talking and a person is never mistaken for the world.
	 */
	UFUNCTION()
	void Cried(const FIntervalCry& Cry);

	/**
	 * WHAT THE WORLD SAID BACK, in the chat, where a player is looking.
	 *
	 * The window had a feed and drew it with `AddOnScreenDebugMessage`, which
	 * is a debugging facility and not an interface: it does not survive a
	 * screenshot, it is not sent over Pixel Streaming in any reliable way, and
	 * it looks like engine diagnostics when it is seen at all. The practical
	 * effect was that when the world REFUSED a deed -- and a world of rules
	 * refuses constantly, which is the point of it -- the citizen simply did
	 * not move and the window said nothing whatever. A player is left clicking
	 * at a screen that appears to have stopped working.
	 *
	 * So the world's own words go in the chat box, which is already on screen
	 * and is where this genre has always put them. A refusal is tinted so it
	 * reads as the world answering rather than as somebody talking.
	 */
	UFUNCTION()
	void Told(const FIntervalFeedLine& Word);

	UFUNCTION()
	void Said(const FText& Text, ETextCommit::Type How);

	UPROPERTY() TObjectPtr<UIntervalBridgeSubsystem> Bridge;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;
	/** What this citizen has seen of the island, kept between sessions. */
	UPROPERTY() TObjectPtr<class UIntervalMemorySubsystem> Memory;

	/** How many pack slots the world gives a citizen. */
	UPROPERTY() int32 PackSlots = 12;

	/** Which sheet is open, or -1 for none. */
	void OpenSheet(int32 Which);

	/** True when the cursor is over a panel and the world must not answer. */
	bool PointerIsOverPanels() const;

	/**
	 * The five places a citizen may wear something, in the order the body
	 * wears them. Read off `AIntervalPanel` rather than invented again.
	 */
	UPROPERTY() TArray<FString> WornOrder = { TEXT("head"), TEXT("body"),
		TEXT("legs"), TEXT("weapon"), TEXT("offhand") };

	/** The two books. A citizen carries one; which one the frame says. */
	UPROPERTY() TArray<FString> CommonBook = { TEXT("still"), TEXT("seal"),
		TEXT("transmute"), TEXT("mend"), TEXT("mendp"), TEXT("unmake"), TEXT("anchor") };
	UPROPERTY() TArray<FString> BarrowBook = { TEXT("waking"), TEXT("rot"),
		TEXT("taking"), TEXT("withering"), TEXT("still"), TEXT("seal"),
		TEXT("unmake") };

	/**
	 * SHOW THE POINTER AND WHAT IT DOES.
	 *
	 * Pixel Streaming sends the VIEWPORT, and the operating system's cursor is
	 * not in the viewport -- so somebody watching this window over the stream
	 * sees things happen with no visible cause: a citizen sets off walking and
	 * nothing said why. The window therefore draws its own pointer, and says
	 * what was pressed, so a watcher can follow a session.
	 *
	 * It is not a debug overlay. A person playing on a phone through the
	 * stream needs exactly the same thing.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interval|Hud")
	bool bShowPointer = true;

	/** The map in the corner. Public so the actor can hand it the bridge. */
	UPROPERTY() TObjectPtr<UIntervalMapWidget> Map;
	/** The whole island, behind the fourth door. */
	UPROPERTY() TObjectPtr<UIntervalWorldMapWidget> WorldMap;
	UPROPERTY() TObjectPtr<class UBorder> WorldPlate;
	/** The map and its caption, so the caption is the map's width by build. */
	UPROPERTY() TObjectPtr<class UVerticalBox> MapColumn;

private:
	void Line(const FString& Who, const FString& What, const FLinearColor& Tint);

	/**
	 * A line of speech: who said it, what they are, where they were, and on
	 * which of the world's two channels. Built differently from `Line`
	 * because the speaker's part and the said part want different colours,
	 * and because the said part is the one that has to wrap.
	 */
	void SpeechLine(const FIntervalSaid& Talk, bool bMine);

	/** `near` or `far` -- which channel the next thing typed will go out on. */
	UPROPERTY() FString Channel = TEXT("near");

	UFUNCTION() void TalkNear();
	UFUNCTION() void TalkFar();

	/**
	 * §0: THE BANNER THAT SAYS WHICH WORLD THIS IS, and the door out of it.
	 *
	 * Nought draws the same island with the same towns, beasts and weather as
	 * the country, which is the whole idea and also its one danger: a resident
	 * who cannot tell the practice from the real thing has been misled by the
	 * window. So while a citizen is in Nought this sits across the top of the
	 * screen and does not scroll, fade or collapse.
	 *
	 * It is also the crossing. The wait is a real five minutes and a resident
	 * is meant to spend it playing, so the countdown lives on the banner
	 * rather than on a card they would have to go and look at -- and when it
	 * ripens the banner says so and takes the click.
	 */
	/**
	 * WHETHER THIS PLAYER WANTS THE WORLD'S OWN HOURS.
	 *
	 * The island runs a day and a night and the night is genuinely dark, which
	 * is the right drawing of a world where a watchfire means something -- and
	 * it is also an hour of somebody's ninety-minute day spent squinting:
	 * "we should probably make the day cycle optional too, so if a player
	 * wants they can just have daylight the entire time".
	 *
	 * It changes NOTHING but pixels. The world's hour is still what every
	 * other window sees, no deed is sent, and the frames say what they said --
	 * which is exactly the licence `ForceDay` was written under.
	 */
	UPROPERTY() bool bAlwaysDay = false;

	UFUNCTION() void Cross();
	UPROPERTY() TObjectPtr<class UButton> CrossTab;
	UPROPERTY() TObjectPtr<UTextBlock> PracticeWord;
	UPROPERTY() TObjectPtr<UTextBlock> CrossWord;
	UPROPERTY() TObjectPtr<class UBorder> PracticePlate;
	/** Whether a knock has already gone out, so the wait is not restarted. */
	/**
	 * §0: WHEN THIS WINDOW LAST KNOCKED, not WHETHER it ever did.
	 *
	 * This was a bool, set true on the first knock and never cleared, so the
	 * window asked the world to let it in exactly once per run. If that one
	 * knock did not land -- the bridge still waking, the node busy, the world
	 * mid-refound -- the plate went on saying "knocking at the world…" for
	 * ever while nothing was being sent, and the only way in was to press the
	 * gate's own key by hand without being told to.
	 *
	 * That happened on a live evening: nine minutes of a window claiming to be
	 * knocking, and the wait did not begin until a person pressed something.
	 *
	 * The bridge was built for the opposite and says so over its handler --
	 * "safe to send every interval: it knocks when there is nothing to wait
	 * on, says so while the wait ripens, and crosses the moment it may". So
	 * this asks again, on a slow clock, until the world answers.
	 */
	double KnockedAt = -1e9;
	void ShowChannel();

	UPROPERTY() TObjectPtr<class UButton> NearTab;
	UPROPERTY() TObjectPtr<class UButton> FarTab;
	UPROPERTY() TObjectPtr<UTextBlock> NearWord;
	UPROPERTY() TObjectPtr<UTextBlock> FarWord;
	void Pressed(const FString& What);
	void FillSheet();

	UPROPERTY() TObjectPtr<UScrollBox> Said_;
	UPROPERTY() TObjectPtr<UEditableTextBox> Entry;
	UPROPERTY() TObjectPtr<UUniformGridPanel> Slots;

	/**
	 * WHAT THIS CITIZEN HAS LEARNED, ABOVE THE PACK, ALWAYS.
	 *
	 * The nine crafts were behind a tab, which makes them something you go and
	 * check rather than something you are watching -- and they are the whole
	 * shape of a day in this world: "i am wondering if skills should always be
	 * visible too, above the pack".
	 *
	 * Drawn as ICONS because nine words in a column three slots wide is a
	 * wall of text at the edge of the screen. Each craft borrows the sprite of
	 * the tool it is practised with -- woodcraft is the hatchet, earthcraft
	 * the pickaxe -- which needs no new art and says what the craft IS faster
	 * than its name does.
	 */
	UPROPERTY() TObjectPtr<UUniformGridPanel> Crafts;
	UPROPERTY() TArray<TObjectPtr<UTextBlock>> CraftLevels;
	UPROPERTY() TArray<TObjectPtr<class UProgressBar>> CraftBars;
	UPROPERTY() TArray<TObjectPtr<class UOverlay>> CraftRows;

	/**
	 * WHAT A DEED PAID, SAID WHERE IT WAS EARNED.
	 *
	 * The window is told every craft's experience every interval, so what a
	 * deed paid is a subtraction and needs nothing new from the world. It is
	 * shown on the craft's OWN row rather than over the citizen's head, which
	 * answers "which trade was that" without a label and puts the number
	 * beside the bar it just moved.
	 *
	 * The rows are nine deep at ten point, so the number rises a few pixels
	 * and fades inside its own row. A drop that climbed the way this genre's
	 * do would be sitting on the row above before it faded.
	 */
	UPROPERTY() TArray<TObjectPtr<UTextBlock>> CraftGains;
	/** When each row's number appeared, and what it has added up to since. */
	TArray<double> GainAt;
	TArray<int32> GainSum;
	/**
	 * The experience each craft had last interval. Empty on the first frame of
	 * a session, which is deliberate: a citizen who arrives with nine crafts
	 * already earned has not just earned them, and nine numbers at the gate
	 * would teach them to ignore the one that matters.
	 */
	TMap<FString, int32> XpWas;
	void FillCrafts();

	/**
	 * AND A RUNG CLIMBED IS AN EVENT.
	 *
	 * "When leveling up, there should be a sound and a banner or something so
	 * it becomes like an event." A level is not bookkeeping -- it is the thing
	 * a citizen spent the afternoon on -- and a number quietly changing in a
	 * panel is the least this window could do about it.
	 *
	 * `Rungs` is what each craft stood at on the last frame. Empty means this
	 * is the first frame of the session, where every craft has "just arrived"
	 * at whatever it is and none of it is news.
	 */
	UPROPERTY() TMap<FString, int32> Rungs;
	UPROPERTY() TObjectPtr<class UBorder> RisenPlate;
	UPROPERTY() TObjectPtr<UTextBlock> RisenLine;
	UPROPERTY() TObjectPtr<class USoundBase> RisenCue;
	double RisenAt = 0.0;

	/**
	 * §6g: THE COUNTER, WHICH IS THE PACK'S GRID WITH SOMEBODY ELSE'S THINGS
	 * IN IT.
	 *
	 * It opens whenever the citizen is standing at a bank and shuts when they
	 * step away, without being asked for either time. A bank screen that has
	 * to be opened is a screen a player has to be told about; a counter you
	 * are standing at is a counter you can see, which is how every other thing
	 * in this window works -- the stall's goods appear when you right-click
	 * the stall, and the vault appears when you stand at the vault.
	 *
	 * Drawn with `UIntervalSlotWidget`, the pack's own cell, on purpose: the
	 * same sprites, the same stack counts, the same left-click-does-the-
	 * obvious-thing. A second kind of cell would be a second visual language
	 * for the same idea.
	 */
	UPROPERTY() TObjectPtr<class UBorder> VaultPlate;

	/**
	 * WHOSE HANDS HAVE BEEN ON THIS WORK LATELY.
	 *
	 * §7cy: a furnace, an anvil and a sawpit remember their last five workers
	 * and forget each after a while. The point is coordination -- "to make it
	 * easier to see if someone is actively doing it" -- so it is shown while
	 * the citizen is STANDING THERE, which is when the question is being
	 * asked, and it goes away when they walk off.
	 *
	 * The names are resolved by the bridge, because whoever fed the furnace
	 * half an hour ago may be nowhere near it now and this window only knows
	 * the people it can see. See `handsOn` there.
	 */
	UPROPERTY() TObjectPtr<class UBorder> HandsPlate;
	UPROPERTY() TObjectPtr<UTextBlock> HandsLine;
	void FillHands();

	/**
	 * §6c: DYING, WHICH SHOULD NOT LOOK LIKE ANOTHER STATE.
	 *
	 * The world holds its breath for DEATH_TICKS and then puts the citizen
	 * back at the founding's spawn, whole. The engine's own note beside that
	 * number says "windows may grieve", and this one did not: a body lay down,
	 * everything else carried on, and the most consequential thing that can
	 * happen to a citizen read as a pause.
	 *
	 * "I just feel we need a clear break. It should be obvious you die and it
	 * should feel different than just any other state transition."
	 *
	 * So the whole screen is washed over, the sound ducks, and one plate says
	 * what happened and what happens next, counting down. It is not a box to
	 * dismiss -- nothing in this world waits for a click -- and it lifts by
	 * itself when the world gives the body back.
	 */
	UPROPERTY() TObjectPtr<class UImage> DeathWash;
	UPROPERTY() TObjectPtr<class UBorder> DeathPlate;
	UPROPERTY() TObjectPtr<UTextBlock> DeathWord;
	UPROPERTY() TObjectPtr<UTextBlock> DeathCount;
	/** 0 to 1 through the wash, so the break arrives rather than snapping on. */
	float Grief = 0.f;
	void FillDeath(float DeltaSeconds);
	UPROPERTY() TObjectPtr<UUniformGridPanel> VaultSlots;
	UPROPERTY() TObjectPtr<UTextBlock> VaultHead;
	UPROPERTY() TArray<TObjectPtr<UIntervalSlotWidget>> VaultCells;
	void FillVault();

	/**
	 * §5c: THE TRADE STANDING BETWEEN TWO PEOPLE.
	 *
	 * Offering is a menu -- what to give, then what for -- because that is a
	 * question with an answer. ANSWERING one is not: a citizen has to be shown
	 * what is on the table before they can say yes, and there is nothing in
	 * the world to right-click that would show it. The offer lives on the
	 * other person's record, so even walking up to them and clicking shows
	 * nothing.
	 *
	 * So it announces itself, in the same plate and the same words as
	 * everything else, and takes the answer. It is the only panel in this
	 * window that a player does not open.
	 */
	UPROPERTY() TObjectPtr<class UBorder> TradePlate;
	UPROPERTY() TObjectPtr<UTextBlock> TradeLine;
	UPROPERTY() TObjectPtr<UTextBlock> TradeMine;
	UPROPERTY() TObjectPtr<class UButton> TakeTab;
	UPROPERTY() TObjectPtr<UTextBlock> TakeWord;
	UPROPERTY() TObjectPtr<class UButton> DropTab;
	UPROPERTY() TObjectPtr<UTextBlock> DropWord;
	/**
	 * §5a: THE ONE DEED IN THIS WORLD THAT NEEDS A WORD TYPED.
	 *
	 * A name is lowercase letters, digits and hyphens, at most twelve, unique
	 * for ever, and it costs standing -- there is only one of each, and the
	 * world will not take a second. No menu can offer that: a list of every
	 * name nobody has taken is not a list. So the citizen's own sheet grows a
	 * line to type it on, and only while they are nameless, because a name
	 * once taken cannot be changed and a box that does nothing is worse than
	 * no box.
	 */
	UFUNCTION() void Named(const FText& Typed, ETextCommit::Type How);
	UPROPERTY() TObjectPtr<UEditableTextBox> NameBox;

	/**
	 * THE SUM, WHEN IT IS NOT ONE OF THE ROUND ONES.
	 *
	 * "It should be possible to trade for x gold instead of arbitrary
	 * amounts." A menu cannot take a number, so the price page's last line
	 * parks the offer on the hand and this box asks for the figure.
	 */
	UFUNCTION() void Priced(const FText& Typed, ETextCommit::Type How);
	UPROPERTY() TObjectPtr<UEditableTextBox> PriceBox;

	UFUNCTION() void TakeTrade();
	UFUNCTION() void DropTrade();
	void FillTrade();
	UPROPERTY() TObjectPtr<UTextBlock> Free;
	UPROPERTY() TArray<TObjectPtr<UIntervalSlotWidget>> Cells;
	UPROPERTY() TObjectPtr<UTextBlock> Vitals;
	/** How much of the day's ninety minutes is left, in the world's own bands. */
	UPROPERTY() TObjectPtr<UTextBlock> Allowance;
	/** The world's own tick, under the vitals rather than beside them. */
	UPROPERTY() TObjectPtr<UTextBlock> Clock;
	/** The name of the ground under the citizen, on a plate below the map. */
	UPROPERTY() TObjectPtr<UTextBlock> Hereabouts;
	UPROPERTY() TObjectPtr<class UBorder> WherePlate;
	/**
	 * The two halves of the interface, kept so they can be taken away.
	 *
	 * Nothing the window draws for a citizen belongs on the title card: a pack
	 * with nothing in it, a health bar for somebody who has not been born, and
	 * a minimap of a world nobody has entered are all answers to questions the
	 * player has not asked yet. They are hidden until the gate is crossed.
	 */
	UPROPERTY() TObjectPtr<UBorder> TalkPlate;
	UPROPERTY() TObjectPtr<class USizeBox> Column;
	UPROPERTY() TObjectPtr<UBorder> Sheet;

	/** The box that holds it, in its own slot beside the pack. See the note
	    over SheetBox in IntervalHud.cpp: in the column it grew into the map. */
	UPROPERTY(Transient)
	TObjectPtr<class USizeBox> SheetBox;
	UPROPERTY() TObjectPtr<class UVerticalBox> SheetBody;
	UPROPERTY() TObjectPtr<UTextBlock> SheetHead;
	UPROPERTY() TArray<TObjectPtr<UIntervalTabWidget>> TabButtons;
	int32 OpenTab = -1;
	UPROPERTY() TObjectPtr<class UImage> Pointer;
	FString Hovering;
	float Hovered = 0.f;
	UPROPERTY() TObjectPtr<UTextBlock> Struck;
	UPROPERTY() TObjectPtr<UBorder> StruckPlate;
	double StruckAt = 0.0;
	bool bWasLeft = false;
	bool bWasRight = false;
	int64 LastDrawn = -1;
};

UCLASS()
class INTERVALBRIDGE_API AIntervalHud : public AActor
{
	GENERATED_BODY()

public:
	AIntervalHud();
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
public:
	/** True when the cursor is on a panel; the world must not answer a click. */
	bool PointerIsOverPanels() const
	{
		return Widget && Widget->PointerIsOverPanels();
	}

private:
	UPROPERTY() TObjectPtr<UIntervalHudWidget> Widget;
	UPROPERTY() TObjectPtr<class UIntervalMenuWidget> Menu;
	UPROPERTY() TObjectPtr<AIntervalHand> Hand;
};
