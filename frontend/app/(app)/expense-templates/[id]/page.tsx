"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Formik } from "formik";
import {
  Button,
  FieldError,
  Input,
  Label,
  ListBox,
  Select,
  Spinner,
  TextField,
} from "@heroui/react";
import { ExpenseTemplateSchema } from "@/helpers/schemas";
import { RecurrenceConfigBuilder } from "@/components/expense-templates/recurrence-config-builder";
import {
  getExpenseTemplates,
  editExpenseTemplate,
} from "@/components/expense-templates/actions";
import { getPaymentMethods } from "@/components/payment-methods/actions";
import type { ExpenseTemplate, PaymentMethod } from "@/helpers/types";

const RECURRENCE_DEFAULT: Record<string, Record<string, unknown>> = {
  weekly: {},
  bi_weekly: { interval_days: 14 },
  monthly: {},
  custom: {},
};

export default function EditExpenseTemplatePage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [template, setTemplate] = useState<ExpenseTemplate | null>(null);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getExpenseTemplates(), getPaymentMethods()]).then(
      ([templatesRes, methodsRes]) => {
        if (templatesRes.success) {
          setTemplate(templatesRes.data.find((t) => t.id === id) ?? null);
        }
        if (methodsRes.success) setPaymentMethods(methodsRes.data);
        setLoading(false);
      },
    );
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  if (!template) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <p className="text-default-500">Expense template not found.</p>
        <Button
          variant="ghost"
          onPress={() => router.push("/expense-templates")}
        >
          Back
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-md flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Button
          size="sm"
          variant="ghost"
          onPress={() => router.push("/expense-templates")}
        >
          ← Back
        </Button>
        <h1 className="text-2xl font-bold">Edit Expense Template</h1>
      </div>

      <Formik
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
          payment_method_id: template.payment_method?.id ?? null,
        }}
        validationSchema={ExpenseTemplateSchema}
        onSubmit={async (values, { setSubmitting }) => {
          setError(null);
          const result = await editExpenseTemplate(template.id, {
            description: values.description,
            base_amount: values.base_amount,
            currency: values.currency as any,
            category: values.category as any,
            recurrence_type: values.recurrence_type as any,
            recurrence_config: values.recurrence_config as any,
            payment_method_id: values.payment_method_id,
          });
          if (result.success) {
            router.push("/expense-templates");
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
        }) => (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <TextField
              isInvalid={!!errors.description && !!touched.description}
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
              isInvalid={!!errors.base_amount && !!touched.base_amount}
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
                <p className="text-xs text-danger">{errors.currency}</p>
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
              <Label>Category</Label>
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
                <p className="text-xs text-danger">{errors.category}</p>
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
              isInvalid={!!errors.recurrence_type && !!touched.recurrence_type}
              fullWidth
            >
              <Label>Recurrence</Label>
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
                <p className="text-xs text-danger">{errors.recurrence_type}</p>
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
                      <ListBox.Item key={m.id} id={m.id} textValue={m.name}>
                        {m.name}
                      </ListBox.Item>
                    ))}
                </ListBox>
              </Select.Popover>
            </Select.Root>

            {error && <p className="text-sm text-danger">{error}</p>}

            <div className="flex gap-2">
              <Button
                variant="ghost"
                onPress={() => router.push("/expense-templates")}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" isDisabled={isSubmitting}>
                {isSubmitting ? <Spinner size="sm" /> : "Save Changes"}
              </Button>
            </div>
          </form>
        )}
      </Formik>
    </div>
  );
}
