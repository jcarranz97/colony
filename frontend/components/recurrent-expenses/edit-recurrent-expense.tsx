"use client";
import { useState } from "react";
import { Formik } from "formik";
import {
  Button,
  Calendar,
  DateField,
  DatePicker,
  FieldError,
  Input,
  Label,
  ListBox,
  Modal,
  Select,
  Spinner,
  TextField,
  Tooltip,
} from "@heroui/react";
import { parseDate } from "@internationalized/date";
import type { DateValue } from "react-aria-components";
import { FiInfo } from "react-icons/fi";
import { RecurrentExpenseSchema } from "@/helpers/schemas";
import { RecurrenceConfigBuilder } from "./recurrence-config-builder";
import { editRecurrentExpense } from "./actions";
import type { RecurrentExpense, PaymentMethod } from "@/helpers/types";
import { formatPaymentMethodName } from "@/helpers/formatters";

interface EditRecurrentExpenseProps {
  template: RecurrentExpense | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: (template: RecurrentExpense) => void;
  paymentMethods: PaymentMethod[];
}

const RECURRENCE_DEFAULT: Record<string, Record<string, unknown>> = {
  weekly: {},
  bi_weekly: { interval_days: 14 },
  monthly: {},
  custom: {},
};

export function EditRecurrentExpense({
  template,
  isOpen,
  onClose,
  onUpdated,
  paymentMethods,
}: EditRecurrentExpenseProps) {
  const [error, setError] = useState<string | null>(null);
  const [confirmDiscard, setConfirmDiscard] = useState(false);
  // After a successful template-only save, hold the saved data and last
  // submitted payload so we can optionally re-submit with propagation.
  const [savedTemplate, setSavedTemplate] = useState<RecurrentExpense | null>(
    null,
  );
  const [propagatePayload, setPropagatePayload] = useState<
    Parameters<typeof editRecurrentExpense>[1] | null
  >(null);
  const [showPropagateDialog, setShowPropagateDialog] = useState(false);
  const [isPropagating, setIsPropagating] = useState(false);
  const [propagateError, setPropagateError] = useState<string | null>(null);

  if (!template) return null;

  return (
    <Formik
      key={template.id}
      initialValues={{
        description: template.description,
        base_amount: template.base_amount,
        currency: template.currency,
        category: template.category,
        recurrence_type: template.recurrence_type,
        recurrence_config: template.recurrence_config as Record<
          string,
          unknown
        >,
        reference_date: template.reference_date,
        payment_method_id: template.payment_method?.id ?? null,
      }}
      validationSchema={RecurrentExpenseSchema}
      onSubmit={async (values, { setSubmitting }) => {
        setError(null);
        const payload = {
          description: values.description,
          base_amount: values.base_amount,
          currency: values.currency as any,
          category: values.category as any,
          recurrence_type: values.recurrence_type as any,
          recurrence_config: values.recurrence_config as any,
          reference_date: values.reference_date,
          payment_method_id: values.payment_method_id,
        };
        const result = await editRecurrentExpense(template.id, payload);
        if (result.success) {
          // Template saved — now ask whether to propagate to open cycles.
          setSavedTemplate(result.data);
          setPropagatePayload(payload);
          setShowPropagateDialog(true);
        } else {
          setError(result.error.message);
        }
        setSubmitting(false);
      }}
    >
      {({
        values,
        errors,
        touched,
        setFieldValue,
        handleSubmit,
        isSubmitting,
        dirty,
      }) => (
        <>
          <Modal.Root
            isOpen={isOpen}
            onOpenChange={(open) => {
              if (!open) {
                setConfirmDiscard(false);
                onClose();
              }
            }}
          >
            <Modal.Backdrop isDismissable={!dirty}>
              <Modal.Container>
                <Modal.Dialog>
                  <form onSubmit={handleSubmit}>
                    <Modal.Header>
                      <Modal.Heading>Edit Recurrent Expense</Modal.Heading>
                    </Modal.Header>
                    <Modal.Body className="flex flex-col gap-4">
                      <TextField
                        isInvalid={
                          !!errors.description && !!touched.description
                        }
                        value={values.description}
                        onChange={(v) => setFieldValue("description", v)}
                      >
                        <Label>Name</Label>
                        <Input />
                        {touched.description && errors.description && (
                          <FieldError>{errors.description}</FieldError>
                        )}
                      </TextField>

                      <TextField
                        isInvalid={
                          !!errors.base_amount && !!touched.base_amount
                        }
                        value={values.base_amount}
                        onChange={(v) => setFieldValue("base_amount", v)}
                      >
                        <Label>Amount</Label>
                        <Input type="number" />
                        {touched.base_amount && errors.base_amount && (
                          <FieldError>{errors.base_amount}</FieldError>
                        )}
                      </TextField>

                      <Select.Root
                        selectedKey={values.currency || null}
                        onSelectionChange={(key) =>
                          setFieldValue("currency", String(key))
                        }
                        isInvalid={!!errors.currency && !!touched.currency}
                        fullWidth
                      >
                        <Label>Currency</Label>
                        <Select.Trigger>
                          <Select.Value>
                            {({ isPlaceholder, selectedText }: any) =>
                              isPlaceholder ? (
                                <span className="text-default-400">
                                  Select currency...
                                </span>
                              ) : (
                                selectedText
                              )
                            }
                          </Select.Value>
                          <Select.Indicator />
                        </Select.Trigger>
                        {touched.currency && errors.currency && (
                          <p className="text-xs text-danger">
                            {errors.currency}
                          </p>
                        )}
                        <Select.Popover>
                          <ListBox>
                            <ListBox.Item id="USD" textValue="USD">
                              USD
                            </ListBox.Item>
                            <ListBox.Item id="MXN" textValue="MXN">
                              MXN
                            </ListBox.Item>
                          </ListBox>
                        </Select.Popover>
                      </Select.Root>

                      <Select.Root
                        selectedKey={values.category || null}
                        onSelectionChange={(key) =>
                          setFieldValue("category", String(key))
                        }
                        isInvalid={!!errors.category && !!touched.category}
                        fullWidth
                      >
                        <Label className="flex items-center gap-1.5">
                          Category
                          <Tooltip delay={0}>
                            <Button
                              isIconOnly
                              variant="ghost"
                              size="sm"
                              aria-label="More information"
                              className="h-4 w-4 min-w-0 p-0 text-default-400"
                            >
                              <FiInfo size={12} />
                            </Button>
                            <Tooltip.Content>
                              <p className="text-xs max-w-56">
                                <strong>Fixed</strong> — same amount every
                                period (rent, subscriptions).{" "}
                                <strong>Variable</strong> — amount changes each
                                time (groceries, gas).
                              </p>
                            </Tooltip.Content>
                          </Tooltip>
                        </Label>
                        <Select.Trigger>
                          <Select.Value>
                            {({ isPlaceholder, selectedText }: any) =>
                              isPlaceholder ? (
                                <span className="text-default-400">
                                  Select category...
                                </span>
                              ) : (
                                selectedText
                              )
                            }
                          </Select.Value>
                          <Select.Indicator />
                        </Select.Trigger>
                        {touched.category && errors.category && (
                          <p className="text-xs text-danger">
                            {errors.category}
                          </p>
                        )}
                        <Select.Popover>
                          <ListBox>
                            <ListBox.Item id="fixed" textValue="Fixed">
                              Fixed
                            </ListBox.Item>
                            <ListBox.Item id="variable" textValue="Variable">
                              Variable
                            </ListBox.Item>
                          </ListBox>
                        </Select.Popover>
                      </Select.Root>

                      <Select.Root
                        selectedKey={values.recurrence_type || null}
                        onSelectionChange={(key) => {
                          const rt = String(key);
                          setFieldValue("recurrence_type", rt);
                          setFieldValue(
                            "recurrence_config",
                            RECURRENCE_DEFAULT[rt] ?? {},
                          );
                        }}
                        isInvalid={
                          !!errors.recurrence_type && !!touched.recurrence_type
                        }
                        fullWidth
                      >
                        <Label className="flex items-center gap-1.5">
                          Recurrence
                          <Tooltip delay={0}>
                            <Button
                              isIconOnly
                              variant="ghost"
                              size="sm"
                              aria-label="More information"
                              className="h-4 w-4 min-w-0 p-0 text-default-400"
                            >
                              <FiInfo size={12} />
                            </Button>
                            <Tooltip.Content>
                              <p className="text-xs max-w-56">
                                How often this expense repeats.{" "}
                                <strong>Bi-weekly</strong> uses a fixed interval
                                of days. <strong>Custom</strong> lets you set
                                any interval and unit.
                              </p>
                            </Tooltip.Content>
                          </Tooltip>
                        </Label>
                        <Select.Trigger>
                          <Select.Value>
                            {({ isPlaceholder, selectedText }: any) =>
                              isPlaceholder ? (
                                <span className="text-default-400">
                                  Select recurrence...
                                </span>
                              ) : (
                                selectedText
                              )
                            }
                          </Select.Value>
                          <Select.Indicator />
                        </Select.Trigger>
                        {touched.recurrence_type && errors.recurrence_type && (
                          <p className="text-xs text-danger">
                            {errors.recurrence_type}
                          </p>
                        )}
                        <Select.Popover>
                          <ListBox>
                            <ListBox.Item id="weekly" textValue="Weekly">
                              Weekly
                            </ListBox.Item>
                            <ListBox.Item id="bi_weekly" textValue="Bi-weekly">
                              Bi-weekly
                            </ListBox.Item>
                            <ListBox.Item id="monthly" textValue="Monthly">
                              Monthly
                            </ListBox.Item>
                            <ListBox.Item id="custom" textValue="Custom">
                              Custom
                            </ListBox.Item>
                          </ListBox>
                        </Select.Popover>
                      </Select.Root>

                      {values.recurrence_type && <RecurrenceConfigBuilder />}

                      <DatePicker
                        value={
                          values.reference_date
                            ? parseDate(values.reference_date)
                            : null
                        }
                        onChange={(date: DateValue | null) => {
                          if (date) {
                            const y = date.year;
                            const m = String(date.month).padStart(2, "0");
                            const d = String(date.day).padStart(2, "0");
                            setFieldValue("reference_date", `${y}-${m}-${d}`);
                          } else {
                            setFieldValue("reference_date", "");
                          }
                        }}
                        isInvalid={
                          !!errors.reference_date && !!touched.reference_date
                        }
                      >
                        <Label className="flex items-center gap-1.5">
                          Start Date
                          <Tooltip delay={0}>
                            <Button
                              isIconOnly
                              variant="ghost"
                              size="sm"
                              aria-label="More information"
                              className="h-4 w-4 min-w-0 p-0 text-default-400"
                            >
                              <FiInfo size={12} />
                            </Button>
                            <Tooltip.Content>
                              <p className="text-xs max-w-56">
                                The most recent date this expense actually
                                occurred. The system uses it as an anchor to
                                calculate which dates fall inside each 6-week
                                cycle. Use the first payment date if unsure.
                              </p>
                            </Tooltip.Content>
                          </Tooltip>
                        </Label>
                        <DateField.Group fullWidth>
                          <DateField.Input>
                            {(segment) => (
                              <DateField.Segment segment={segment} />
                            )}
                          </DateField.Input>
                          <DateField.Suffix>
                            <DatePicker.Trigger>
                              <DatePicker.TriggerIndicator />
                            </DatePicker.Trigger>
                          </DateField.Suffix>
                        </DateField.Group>
                        {touched.reference_date && errors.reference_date && (
                          <FieldError>{errors.reference_date}</FieldError>
                        )}
                        <DatePicker.Popover>
                          <Calendar aria-label="Start date">
                            <Calendar.Header>
                              <Calendar.YearPickerTrigger>
                                <Calendar.YearPickerTriggerHeading />
                                <Calendar.YearPickerTriggerIndicator />
                              </Calendar.YearPickerTrigger>
                              <Calendar.NavButton slot="previous" />
                              <Calendar.NavButton slot="next" />
                            </Calendar.Header>
                            <Calendar.Grid>
                              <Calendar.GridHeader>
                                {(day) => (
                                  <Calendar.HeaderCell>
                                    {day}
                                  </Calendar.HeaderCell>
                                )}
                              </Calendar.GridHeader>
                              <Calendar.GridBody>
                                {(date) => <Calendar.Cell date={date} />}
                              </Calendar.GridBody>
                            </Calendar.Grid>
                            <Calendar.YearPickerGrid>
                              <Calendar.YearPickerGridBody>
                                {({ year }) => (
                                  <Calendar.YearPickerCell year={year} />
                                )}
                              </Calendar.YearPickerGridBody>
                            </Calendar.YearPickerGrid>
                          </Calendar>
                        </DatePicker.Popover>
                      </DatePicker>

                      <Select.Root
                        selectedKey={values.payment_method_id ?? "none"}
                        onSelectionChange={(key) =>
                          setFieldValue(
                            "payment_method_id",
                            key === "none" ? null : String(key),
                          )
                        }
                        fullWidth
                      >
                        <Label>Payment Method (optional)</Label>
                        <Select.Trigger>
                          <Select.Value>
                            {({ isPlaceholder, selectedText }: any) =>
                              isPlaceholder ? (
                                <span className="text-default-400">None</span>
                              ) : (
                                selectedText
                              )
                            }
                          </Select.Value>
                          <Select.Indicator />
                        </Select.Trigger>
                        <Select.Popover>
                          <ListBox>
                            <ListBox.Item id="none" textValue="None">
                              None
                            </ListBox.Item>
                            {paymentMethods
                              .filter((m) => m.active)
                              .map((m) => (
                                <ListBox.Item
                                  key={m.id}
                                  id={m.id}
                                  textValue={formatPaymentMethodName(m)}
                                >
                                  {formatPaymentMethodName(m)}
                                </ListBox.Item>
                              ))}
                          </ListBox>
                        </Select.Popover>
                      </Select.Root>

                      {error && <p className="text-sm text-danger">{error}</p>}
                    </Modal.Body>
                    {confirmDiscard ? (
                      <Modal.Footer className="gap-2 flex-col items-start">
                        <p
                          className="text-sm"
                          style={{ fontFamily: "var(--font-hand)" }}
                        >
                          You have unsaved changes. Discard them?
                        </p>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            onPress={() => setConfirmDiscard(false)}
                          >
                            Keep Editing
                          </Button>
                          <Button
                            variant="danger"
                            onPress={() => {
                              setConfirmDiscard(false);
                              onClose();
                            }}
                          >
                            Discard
                          </Button>
                        </div>
                      </Modal.Footer>
                    ) : (
                      <Modal.Footer className="gap-2">
                        <Button
                          variant="ghost"
                          onPress={() => {
                            if (dirty) setConfirmDiscard(true);
                            else onClose();
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          type="submit"
                          variant="primary"
                          isDisabled={isSubmitting}
                        >
                          {isSubmitting ? <Spinner size="sm" /> : "Save"}
                        </Button>
                      </Modal.Footer>
                    )}
                  </form>
                </Modal.Dialog>
              </Modal.Container>
            </Modal.Backdrop>
          </Modal.Root>

          {/* Propagation confirmation dialog — shown after template is saved */}
          <Modal.Root
            isOpen={showPropagateDialog}
            onOpenChange={(open) => {
              if (!open) {
                // "No, template only" path — close everything
                if (savedTemplate) onUpdated(savedTemplate);
                setShowPropagateDialog(false);
                setSavedTemplate(null);
                setPropagatePayload(null);
                setPropagateError(null);
                onClose();
              }
            }}
          >
            <Modal.Backdrop isDismissable={false}>
              <Modal.Container>
                <Modal.Dialog>
                  <Modal.Header>
                    <Modal.Heading>Apply changes to open cycles?</Modal.Heading>
                  </Modal.Header>
                  <Modal.Body>
                    <p className="text-sm">
                      Do you also want to update all unpaid expenses in open
                      cycles that were generated from this template?
                    </p>
                    {propagateError && (
                      <p className="text-sm text-danger mt-2">
                        {propagateError}
                      </p>
                    )}
                  </Modal.Body>
                  <Modal.Footer className="gap-2">
                    <Button
                      variant="ghost"
                      isDisabled={isPropagating}
                      onPress={() => {
                        // No — accept the template-only save and close
                        if (savedTemplate) onUpdated(savedTemplate);
                        setShowPropagateDialog(false);
                        setSavedTemplate(null);
                        setPropagatePayload(null);
                        setPropagateError(null);
                        onClose();
                      }}
                    >
                      No, template only
                    </Button>
                    <Button
                      variant="primary"
                      isDisabled={isPropagating}
                      onPress={async () => {
                        if (!propagatePayload) return;
                        setIsPropagating(true);
                        setPropagateError(null);
                        const result = await editRecurrentExpense(
                          template.id,
                          propagatePayload,
                          true,
                        );
                        setIsPropagating(false);
                        if (result.success) {
                          onUpdated(result.data);
                          setShowPropagateDialog(false);
                          setSavedTemplate(null);
                          setPropagatePayload(null);
                          onClose();
                        } else {
                          setPropagateError(result.error.message);
                        }
                      }}
                    >
                      {isPropagating ? (
                        <Spinner size="sm" />
                      ) : (
                        "Yes, update open cycles"
                      )}
                    </Button>
                  </Modal.Footer>
                </Modal.Dialog>
              </Modal.Container>
            </Modal.Backdrop>
          </Modal.Root>
        </>
      )}
    </Formik>
  );
}
