import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  LabelBuilder,
  MessageFlags,
  ModalBuilder,
  PermissionFlagsBits,
  TextInputBuilder,
  TextInputStyle,
  type ModalSubmitInteraction,
} from "discord.js";

import { customId, defineComponent } from "#core/components.ts";
import { UserError } from "#core/errors.ts";
import { successEmbed } from "#shared/ui/embeds.ts";

import { parseColor } from "../embed-colors.ts";
import { customEmbed } from "../tools.views.ts";

const FIELDS = { title: "title", text: "text", color: "color" } as const;

const input = (id: string, style: TextInputStyle, maxLength: number) =>
  new TextInputBuilder().setCustomId(id).setStyle(style).setMaxLength(maxLength);

function editorModal(color: string): ModalBuilder {
  const colorInput = input(FIELDS.color, TextInputStyle.Short, 20)
    .setRequired(false)
    .setPlaceholder("red or #ff8800");
  return new ModalBuilder()
    .setCustomId(customId(embedEditor, "submit"))
    .setTitle("New embed")
    .addLabelComponents(
      new LabelBuilder()
        .setLabel("Title")
        .setTextInputComponent(input(FIELDS.title, TextInputStyle.Short, 256).setRequired(false)),
      new LabelBuilder()
        .setLabel("Text")
        .setTextInputComponent(input(FIELDS.text, TextInputStyle.Paragraph, 4000)),
      new LabelBuilder()
        .setLabel("Color")
        .setTextInputComponent(color === "" ? colorInput : colorInput.setValue(color)),
    );
}

async function post(interaction: ModalSubmitInteraction<"cached">): Promise<void> {
  const field = (id: string) => interaction.fields.getTextInputValue(id).trim();
  const colorText = field(FIELDS.color);
  const color = colorText === "" ? undefined : parseColor(colorText);
  if (color === undefined && colorText !== "") {
    throw new UserError(`\`${colorText}\` is not a color. Use a name such as red or a hex code.`);
  }
  if (!interaction.channel) throw new UserError("I can't post in this channel.");
  await interaction.channel.send({
    embeds: [customEmbed({ text: field(FIELDS.text), title: field(FIELDS.title), color })],
  });
  const done = { embeds: [successEmbed("Embed posted.")], components: [] };
  await (interaction.isFromMessage()
    ? interaction.update(done)
    : interaction.reply({ ...done, flags: MessageFlags.Ephemeral }));
}

/** Opens the embed modal from a button and posts the result. Slash commands can't open it yet. */
export const embedEditor = defineComponent({
  id: "embed-editor",
  run: async (interaction, [step, color = ""]) => {
    if (!interaction.memberPermissions.has(PermissionFlagsBits.Administrator)) {
      throw new UserError("You need the Administrator permission to post embeds.");
    }
    if (step === "open" && interaction.isButton()) {
      await interaction.showModal(editorModal(color));
    } else if (step === "submit" && interaction.isModalSubmit()) {
      await post(interaction);
    }
  },
});

/** A button that opens the editor, with the color field filled in when one was given. */
export const openEditorRow = (color: number | undefined) =>
  new ActionRowBuilder<ButtonBuilder>().addComponents(
    new ButtonBuilder()
      .setCustomId(
        customId(
          embedEditor,
          "open",
          color === undefined ? "" : `#${color.toString(16).padStart(6, "0")}`,
        ),
      )
      .setLabel("Open editor")
      .setStyle(ButtonStyle.Primary),
  );
